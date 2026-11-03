"""Regras das contas a receber: o limite de crédito do cliente, as parcelas do carnê e o recebimento delas.

A parcela pode ser paga em qualquer loja, toda ou só uma parte. Os juros de atraso são só sugeridos (o
caixa pode mudar): % ao mês da forma Crediário, contado por dia, sobre o que falta pagar (como no VB6).
"""
import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominios.caixa import servico as caixa
from app.dominios.caixa.modelos import ABERTO, FormaPagamento, LancamentoCaixa
from app.dominios.clientes.modelos import AnotacaoCliente, Cliente, Setor
from app.dominios.receber.esquemas import RecebimentoDados
from app.dominios.receber.modelos import (
    TIPOS_COBRANCA, ContaCobranca, ContaReceber, HistoricoParcela, ItemRecebimento, PagamentoRecebimento, ParcelaReceber, RecebimentoCrediario,
)
from app.nucleo.textos import moeda

ZERO = Decimal("0.00")
CENTAVO = Decimal("0.01")


class ErroReceber(Exception):
    """Erro de regra do recebimento; a mensagem vai para o usuário."""


class NaoEncontrado(ErroReceber):
    pass


class DadoInvalido(ErroReceber):
    pass


@dataclass
class Credito:
    limite: Decimal
    em_aberto: Decimal  # parcelas em aberto em todas as lojas (o prejuízo também: o cliente continua devendo)
    disponivel: Decimal
    em_prejuizo: Decimal
    bloqueado: bool
    suspenso: bool

    @property
    def impedimento(self) -> str | None:
        """Por que o cliente não pode comprar no crediário, mesmo com autorização."""
        if self.bloqueado:
            return "O cliente está bloqueado e não pode comprar no crediário"
        if self.suspenso:
            return "O crédito do cliente está suspenso"
        return None


def em_aberto(db: Session, cliente_id: int) -> Decimal:
    total = db.scalar(select(func.sum(ParcelaReceber.aberto)).join(ContaReceber)
                      .where(ContaReceber.cliente_id == cliente_id))
    return Decimal(total or 0).quantize(CENTAVO)


def em_prejuizo(db: Session, cliente_id: int) -> Decimal:
    total = db.scalar(select(func.sum(ParcelaReceber.aberto)).join(ContaReceber)
                      .where(ContaReceber.cliente_id == cliente_id, ParcelaReceber.prejuizo_em.is_not(None)))
    return Decimal(total or 0).quantize(CENTAVO)


def credito(db: Session, cliente: Cliente) -> Credito:
    """O limite restante é o limite do cliente menos tudo o que ele tem em aberto, em qualquer loja. O que caiu
    no prejuízo conta também, como no VB6: quem deu prejuízo não compra no crediário sem a gerência."""
    aberto = em_aberto(db, cliente.id)
    return Credito(limite=cliente.limite_credito, em_aberto=aberto, disponivel=cliente.limite_credito - aberto,
                   em_prejuizo=em_prejuizo(db, cliente.id), bloqueado=cliente.bloqueado,
                   suspenso=cliente.credito_suspenso)


def somar_meses(inicio: date, meses: int) -> date:
    mes = inicio.month - 1 + meses
    ano, mes = inicio.year + mes // 12, mes % 12 + 1
    return date(ano, mes, min(inicio.day, calendar.monthrange(ano, mes)[1]))


def vencimentos(primeiro: date, parcelas: int, intervalo: int) -> list[date]:
    """Intervalo de 30 dias (ou múltiplo) vence no mesmo dia de cada mês, como no VB6; outro, a cada tantos dias."""
    if intervalo % 30 == 0:
        return [somar_meses(primeiro, i * intervalo // 30) for i in range(parcelas)]
    return [primeiro + timedelta(days=i * intervalo) for i in range(parcelas)]


def dividir(valor: Decimal, parcelas: int) -> list[Decimal]:
    """Parcelas iguais, sem juros; os centavos que sobram vão na última."""
    parcela = (valor / parcelas).quantize(CENTAVO, rounding=ROUND_DOWN)
    return [parcela] * (parcelas - 1) + [valor - parcela * (parcelas - 1)]


GERAL = "Geral"


def conta_padrao(db: Session) -> ContaCobranca:
    """A conta de cobrança padrão (Geral): o carnê está na loja, sem estar com ninguém."""
    conta = db.scalar(select(ContaCobranca).where(ContaCobranca.padrao.is_(True)))
    if conta is None:
        conta = ContaCobranca(nome=GERAL, padrao=True, ativo=True)
        db.add(conta)
        db.flush()
    return conta


def lancar_carne(db: Session, empresa_id: int, cliente_id: int, venda_id: int | None, valor: Decimal,
                 parcelas: int, primeiro_vencimento: date, intervalo: int, historico: str,
                 usuario_id: int, tipo_cobranca: str | None = None) -> ContaReceber:
    """Cria a conta e as parcelas; quem chama grava."""
    conta = ContaReceber(empresa_id=empresa_id, cliente_id=cliente_id, venda_id=venda_id, valor=valor,
                         historico=historico[:80], usuario_id=usuario_id)
    datas = vencimentos(primeiro_vencimento, parcelas, intervalo)
    geral = conta_padrao(db)
    for numero, (vencimento, parte) in enumerate(zip(datas, dividir(valor, parcelas)), start=1):
        conta.parcelas.append(ParcelaReceber(numero=numero, vencimento=vencimento, vencimento_inicial=vencimento,
                                             valor=parte, aberto=parte, conta_cobranca=geral, tipo_cobranca=tipo_cobranca))
    db.add(conta)
    return conta


def conta_da_venda(db: Session, venda_id: int) -> ContaReceber | None:
    return db.scalar(select(ContaReceber).where(ContaReceber.venda_id == venda_id))


# ------------------------------------------------------------ receber parcelas

def juros_ao_mes(db: Session) -> Decimal:
    """O % ao mês de juros de atraso, da forma Crediário (o juros_par do VB6)."""
    taxa = db.scalar(select(FormaPagamento.juros_atraso).where(FormaPagamento.tipo == "crediario")
                     .order_by(FormaPagamento.ativo.desc(), FormaPagamento.id))
    return taxa or ZERO


def juros_sugerido(aberto: Decimal, vencimento: date, taxa: Decimal, hoje: date | None = None) -> tuple[int, Decimal]:
    """Dias de atraso e os juros: o % ao mês dividido por 30, vezes os dias, sobre o que falta pagar."""
    dias = ((hoje or date.today()) - vencimento).days
    if dias <= 0:
        return 0, ZERO
    return dias, (aberto * taxa / 100 / 30 * dias).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def parcelas_abertas(db: Session, cliente_id: int) -> list[ParcelaReceber]:
    """O que o cliente tem para pagar, em todas as lojas, do vencimento mais antigo ao mais novo."""
    if db.get(Cliente, cliente_id) is None:
        raise NaoEncontrado("Cliente não encontrado")
    return list(db.scalars(
        select(ParcelaReceber).join(ContaReceber)
        .where(ContaReceber.cliente_id == cliente_id, ParcelaReceber.aberto > 0)
        .order_by(ParcelaReceber.vencimento, ParcelaReceber.id)))


def _documento(recebimento: RecebimentoCrediario) -> str:
    return f"crediário {recebimento.id}"


def receber(db: Session, empresa_id: int, usuario_id: int, dados: RecebimentoDados) -> RecebimentoCrediario:
    """O caixa recebe parcelas do cliente (de qualquer loja): abate do que falta de cada uma e lança no caixa,
    em cada forma em que o cliente pagou."""
    try:
        sessao = caixa.obter_sessao(db, empresa_id, dados.sessao_caixa_id)
    except caixa.ErroCaixa as e:
        raise NaoEncontrado(str(e))
    if sessao.situacao != ABERTO:
        raise DadoInvalido(f"O caixa {sessao.caixa.nome} está fechado")
    cliente = db.get(Cliente, dados.cliente_id)
    if cliente is None:
        raise NaoEncontrado("Cliente não encontrado")

    recebimento = RecebimentoCrediario(empresa_id=empresa_id, sessao_caixa_id=sessao.id, cliente_id=dados.cliente_id,
                                       usuario_id=usuario_id)
    vistas = set()
    for item in dados.itens:
        parcela = db.get(ParcelaReceber, item.parcela_id)
        if parcela is None or parcela.conta.cliente_id != dados.cliente_id:
            raise NaoEncontrado("Parcela não encontrada")
        if parcela.id in vistas:
            raise DadoInvalido(f"A parcela {parcela.numero} entrou duas vezes")
        vistas.add(parcela.id)
        if item.valor > parcela.aberto:
            raise DadoInvalido(f"Da parcela {parcela.numero}/{len(parcela.conta.parcelas)} faltam só "
                               f"{moeda(parcela.aberto)}")
        parcela.aberto -= item.valor
        recebimento.itens.append(ItemRecebimento(parcela=parcela, valor=item.valor, juros=item.juros))

    for pagamento in dados.pagamentos:
        forma = db.get(FormaPagamento, pagamento.forma_pagamento_id)
        if forma is None or not forma.ativo:
            raise NaoEncontrado("Forma de pagamento não encontrada")
        if forma.tipo == "crediario":
            raise DadoInvalido("A parcela do crediário não se paga com crediário")
        recebimento.pagamentos.append(PagamentoRecebimento(forma_pagamento=forma, valor=pagamento.valor))
    total = recebimento.total
    pago = sum((p.valor for p in recebimento.pagamentos), ZERO)
    if pago < total:
        raise DadoInvalido(f"Falta lançar {moeda(total - pago)}")
    if pago > total:
        raise DadoInvalido(f"O lançado passa do total em {moeda(pago - total)}; "
                           "o troco sai do valor que o cliente deu no dinheiro")
    no_dinheiro = sum((p.valor for p in recebimento.pagamentos if p.forma_pagamento.tipo == "dinheiro"), ZERO)
    if no_dinheiro:
        recebimento.valor_recebido = dados.valor_recebido or no_dinheiro
        if recebimento.valor_recebido < no_dinheiro:
            raise DadoInvalido(f"O valor que o cliente deu é menor que os {moeda(no_dinheiro)} no dinheiro")

    if dados.voltar_para_geral:
        geral = conta_padrao(db)
        for conta in {item.parcela.conta for item in recebimento.itens}:
            for parcela in conta.parcelas:
                parcela.conta_cobranca = geral
    db.add(recebimento)
    db.flush()
    for pagamento in recebimento.pagamentos:
        db.add(LancamentoCaixa(sessao_id=sessao.id, tipo="entrada", motivo="crediario",
                               forma_pagamento_id=pagamento.forma_pagamento.id, valor=pagamento.valor,
                               documento=_documento(recebimento), usuario_id=usuario_id,
                               historico=f"Crediário {cliente.nome}"[:80]))
    db.commit()
    db.expire_all()
    return recebimento


def obter(db: Session, empresa_id: int, recebimento_id: int) -> RecebimentoCrediario:
    recebimento = db.get(RecebimentoCrediario, recebimento_id)
    if recebimento is None or recebimento.empresa_id != empresa_id:
        raise NaoEncontrado("Recebimento não encontrado")
    return recebimento


def estornar(db: Session, empresa_id: int, usuario_id: int, recebimento_id: int) -> RecebimentoCrediario:
    """Recebimento errado: as parcelas voltam a dever o que deviam e os lançamentos saem do caixa.
    Só enquanto o caixa em que foi recebido está aberto."""
    recebimento = obter(db, empresa_id, recebimento_id)
    if recebimento.estornado_em is not None:
        raise DadoInvalido("Este recebimento já foi estornado")
    if recebimento.sessao_caixa.situacao != ABERTO:
        raise DadoInvalido("O caixa deste recebimento já foi fechado")
    for item in recebimento.itens:
        item.parcela.aberto += item.valor
    agora = datetime.now()
    for lancamento in recebimento.sessao_caixa.lancamentos:
        if lancamento.documento == _documento(recebimento) and lancamento.estornado_em is None:
            lancamento.estornado_em = agora
            lancamento.estornado_por_id = usuario_id
    recebimento.estornado_em = agora
    recebimento.estornado_por_id = usuario_id
    db.commit()
    db.expire_all()
    return recebimento


# ------------------------------------------------------------ consultar (a tela de contas a receber)

@dataclass
class Filtros:
    """Os filtros da tela de contas a receber (os da frmEditaMov do VB6 que já têm dados aqui)."""

    situacao: str = "aberto"  # aberto, pagas (alguma coisa já paga) ou todas
    empresa_id: int | None = None  # a loja que vendeu; sem ela, todas
    cliente_id: int | None = None
    busca: str | None = None  # nome ou CPF/CNPJ do cliente
    documento: str | None = None  # começo do número do VB6 (ou o id da conta)
    origem: str | None = None
    historico: str | None = None
    data: str = "vencimento"  # vencimento, inicial ou emissao
    de: date | None = None
    ate: date | None = None
    valor: Decimal | None = None  # o que falta, exato
    cidade_id: int | None = None
    setor_id: int | None = None
    orgao_id: int | None = None
    grupo_id: int | None = None
    bloqueio: str | None = None  # bloqueados ou liberados
    credito_suspenso: bool | None = None
    prejuizo: str = "fora"  # fora (o normal, como no VB6), so ou junto
    conta_cobranca_id: int | None = None
    tipo_cobranca: str | None = None


ORDENS = {
    "vencimento": (ParcelaReceber.vencimento, Cliente.nome, ParcelaReceber.numero),
    "cliente": (Cliente.nome, ParcelaReceber.vencimento, ParcelaReceber.numero),
    "documento": (ContaReceber.documento_legado, ContaReceber.id, ParcelaReceber.numero),
    "valor": (ParcelaReceber.valor.desc(), ParcelaReceber.vencimento),
}


def _condicoes(f: Filtros) -> list:
    c = []
    if f.situacao == "aberto":
        c.append(ParcelaReceber.aberto > 0)
    elif f.situacao == "pagas":
        c.append(ParcelaReceber.aberto < ParcelaReceber.valor)
    if f.empresa_id:
        c.append(ContaReceber.empresa_id == f.empresa_id)
    if f.cliente_id:
        c.append(ContaReceber.cliente_id == f.cliente_id)
    if f.busca and f.busca.strip():
        termo = f.busca.strip()
        digitos = termo.replace(".", "").replace("-", "").replace("/", "")
        if digitos.isdigit():
            c.append(Cliente.cpf_cnpj.like(f"{digitos}%"))
        else:
            c.append(Cliente.nome.ilike(f"%{termo}%"))
    if f.documento and f.documento.strip():
        numero = f.documento.strip()
        c.append(ContaReceber.documento_legado.like(f"{numero}%") if not numero.isdigit()
                 else (ContaReceber.documento_legado.like(f"{numero}%")) | (ContaReceber.id == int(numero)))
    if f.origem:
        c.append(ContaReceber.origem == f.origem)
    if f.historico and f.historico.strip():
        c.append(ContaReceber.historico.ilike(f"%{f.historico.strip()}%"))
    campo = {"inicial": ParcelaReceber.vencimento_inicial, "emissao": func.date(ContaReceber.criado_em)}.get(
        f.data, ParcelaReceber.vencimento)
    if f.de:
        c.append(campo >= f.de)
    if f.ate:
        c.append(campo <= f.ate)
    if f.valor is not None:
        c.append(ParcelaReceber.aberto == f.valor)
    if f.setor_id:
        c.append(Cliente.setor_id == f.setor_id)
    if f.cidade_id:
        c.append(Cliente.setor_id.in_(select(Setor.id).where(Setor.cidade_id == f.cidade_id)))
    if f.orgao_id:
        c.append(Cliente.orgao_id == f.orgao_id)
    if f.grupo_id:
        c.append(Cliente.grupo_id == f.grupo_id)
    if f.bloqueio == "bloqueados":
        c.append(Cliente.bloqueado.is_(True))
    elif f.bloqueio == "liberados":
        c.append(Cliente.bloqueado.is_(False))
    if f.credito_suspenso is not None:
        c.append(Cliente.credito_suspenso.is_(f.credito_suspenso))
    if f.conta_cobranca_id:
        c.append(ParcelaReceber.conta_cobranca_id == f.conta_cobranca_id)
    if f.tipo_cobranca:
        c.append(ParcelaReceber.tipo_cobranca == f.tipo_cobranca)
    if f.prejuizo == "fora":
        c.append(ParcelaReceber.prejuizo_em.is_(None))
    elif f.prejuizo == "so":
        c.append(ParcelaReceber.prejuizo_em.is_not(None))
    return c


def consultar(db: Session, f: Filtros, ordem: str, limite: int,
              deslocamento: int) -> tuple[list[ParcelaReceber], int, Decimal, Decimal]:
    """As parcelas que passam nos filtros, de todas as lojas (D9), com o total e as somas da consulta toda."""
    base = select(ParcelaReceber).join(ContaReceber).join(Cliente, Cliente.id == ContaReceber.cliente_id) \
        .where(*_condicoes(f))
    filtradas = base.with_only_columns(ParcelaReceber.valor, ParcelaReceber.aberto).subquery()
    total, soma_valor, soma_aberto = db.execute(
        select(func.count(), func.coalesce(func.sum(filtradas.c.valor), 0),
               func.coalesce(func.sum(filtradas.c.aberto), 0))).one()
    itens = db.scalars(base.order_by(*ORDENS.get(ordem, ORDENS["vencimento"]), ParcelaReceber.id)
                       .limit(limite).offset(deslocamento))
    return list(itens), total, Decimal(soma_valor).quantize(CENTAVO), Decimal(soma_aberto).quantize(CENTAVO)


# ------------------------------------------------------------ prejuízo

def marcar_prejuizo(db: Session, usuario_id: int, parcela_ids: list[int], motivo: str) -> int:
    """As parcelas em aberto caem no prejuízo: saem da lista do contas a receber. Devolve quantas mudaram."""
    agora = datetime.now()
    mudaram = 0
    for parcela in _parcelas(db, parcela_ids):
        if parcela.aberto <= 0:
            raise DadoInvalido(f"A parcela {parcela.conta.documento} {parcela.numero} já está paga")
        if parcela.prejuizo_em is None:
            parcela.prejuizo_em, parcela.prejuizo_por_id, parcela.prejuizo_motivo = agora, usuario_id, motivo
            _historico(db, parcela, "prejuizo", None, "no prejuízo", motivo, usuario_id)
            mudaram += 1
    db.commit()
    return mudaram


def tirar_prejuizo(db: Session, parcela_ids: list[int], usuario_id: int | None = None) -> int:
    """A parcela volta a ser cobrada (no VB6, o mesmo botão marcava e desmarcava)."""
    mudaram = 0
    for parcela in _parcelas(db, parcela_ids):
        if parcela.prejuizo_em is not None:
            _historico(db, parcela, "prejuizo", "no prejuízo", "cobrando de novo", None, usuario_id)
            parcela.prejuizo_em = parcela.prejuizo_por_id = parcela.prejuizo_motivo = None
            mudaram += 1
    db.commit()
    return mudaram


def _parcelas(db: Session, parcela_ids: list[int]) -> list[ParcelaReceber]:
    parcelas = list(db.scalars(select(ParcelaReceber).where(ParcelaReceber.id.in_(parcela_ids))))
    if len(parcelas) != len(set(parcela_ids)):
        raise NaoEncontrado("Parcela não encontrada")
    return parcelas


# ------------------------------------------------------------ contas de cobrança

def listar_contas_cobranca(db: Session) -> list[ContaCobranca]:
    conta_padrao(db)
    return list(db.scalars(select(ContaCobranca).order_by(ContaCobranca.padrao.desc(), ContaCobranca.nome)))


def salvar_conta_cobranca(db: Session, conta_id: int | None, nome: str, ativo: bool) -> ContaCobranca:
    conta = db.get(ContaCobranca, conta_id) if conta_id else ContaCobranca(padrao=False)
    if conta is None:
        raise NaoEncontrado("Conta de cobrança não encontrada")
    outra = db.scalar(select(ContaCobranca).where(func.lower(ContaCobranca.nome) == nome.lower(),
                                                  ContaCobranca.id != (conta.id or 0)))
    if outra is not None:
        raise DadoInvalido(f"Já existe a conta de cobrança {outra.nome}")
    if conta.padrao and not ativo:
        raise DadoInvalido("A conta Geral não pode ser desativada")
    conta.nome, conta.ativo = nome, ativo
    db.add(conta)
    db.commit()
    return conta


def mudar_cobranca(db: Session, parcela_ids: list[int], conta_cobranca_id: int, usuario_id: int | None = None) -> int:
    """Muda as parcelas de conta de cobrança, em lote (entregar ao cobrador, mandar ao advogado, voltar à loja...).
    Devolve quantas mudaram."""
    conta = db.get(ContaCobranca, conta_cobranca_id)
    if conta is None or not conta.ativo:
        raise NaoEncontrado("Conta de cobrança não encontrada")
    mudaram = 0
    for parcela in _parcelas(db, parcela_ids):
        if parcela.conta_cobranca_id != conta.id:
            _historico(db, parcela, "cobranca", parcela.conta_cobranca.nome, conta.nome, None, usuario_id)
            parcela.conta_cobranca = conta
            mudaram += 1
    db.commit()
    return mudaram


def tipo_cobranca_do_cliente(cliente: Cliente) -> str:
    """O tipo de cobrança que a venda sugere: pagamento na loja, ou cobrança no cliente (em casa ou no trabalho)."""
    return "loja" if cliente.forma_cobranca == "loja" else "cliente"


# ------------------------------------------------------------ prorrogar e editar (financeiro)

def _historico(db: Session, parcela: ParcelaReceber, mudanca: str, de: str | None, para: str | None,
               anotacao: str | None, usuario_id: int | None) -> None:
    db.add(HistoricoParcela(parcela_id=parcela.id, mudanca=mudanca, de=de, para=para, anotacao=anotacao,
                            usuario_id=usuario_id))


def _data_br(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


def prorrogar(db: Session, usuario_id: int, parcela_ids: list[int], vencimento: date | None, dias: int | None,
              anotacao: str | None) -> int:
    """Muda o vencimento das parcelas em aberto: para uma data só, ou tantos dias depois do vencimento de cada uma.
    O vencimento inicial fica como estava, e cada prorrogação vai para o histórico. Devolve quantas mudaram."""
    if (vencimento is None) == (dias is None):
        raise DadoInvalido("Informe o novo vencimento ou quantos dias prorrogar")
    mudaram = 0
    for parcela in _parcelas(db, parcela_ids):
        if parcela.aberto <= 0:
            raise DadoInvalido(f"A parcela {parcela.numero} de {parcela.conta.documento} já está paga")
        novo = vencimento or parcela.vencimento + timedelta(days=dias)
        if novo == parcela.vencimento:
            continue
        _historico(db, parcela, "prorrogacao", _data_br(parcela.vencimento), _data_br(novo), anotacao, usuario_id)
        parcela.vencimento_inicial = parcela.vencimento_inicial or parcela.vencimento
        parcela.vencimento = novo
        mudaram += 1
    db.commit()
    return mudaram


def editar_parcela(db: Session, usuario_id: int, parcela_id: int, tipo_cobranca: str | None,
                   conta_cobranca_id: int) -> ParcelaReceber:
    """O tipo e a conta de cobrança da parcela. O que falta pagar não se muda aqui: só com a baixa."""
    parcela = db.get(ParcelaReceber, parcela_id)
    if parcela is None:
        raise NaoEncontrado("Parcela não encontrada")
    if tipo_cobranca != parcela.tipo_cobranca:
        nome = lambda t: TIPOS_COBRANCA[t][0] if t else None  # noqa: E731
        _historico(db, parcela, "tipo", nome(parcela.tipo_cobranca), nome(tipo_cobranca), None, usuario_id)
        parcela.tipo_cobranca = tipo_cobranca
    db.commit()
    if conta_cobranca_id != parcela.conta_cobranca_id:
        mudar_cobranca(db, [parcela.id], conta_cobranca_id, usuario_id)
    db.expire_all()
    return db.get(ParcelaReceber, parcela_id)


def editar_documento(db: Session, usuario_id: int, conta_id: int, historico: str, documento: str | None) -> ContaReceber:
    """O cabeçalho do documento: o histórico e o número. A mudança vai para o histórico de todas as parcelas."""
    conta = db.get(ContaReceber, conta_id)
    if conta is None:
        raise NaoEncontrado("Documento não encontrado")
    antes = f"{conta.documento_legado or ''} · {conta.historico}"
    depois = f"{documento or ''} · {historico}"
    if antes != depois:
        for parcela in conta.parcelas:
            _historico(db, parcela, "documento", antes[:100], depois[:100], None, usuario_id)
        conta.historico, conta.documento_legado = historico, documento
    db.commit()
    return conta


def historico(db: Session, parcela_id: int) -> list[HistoricoParcela]:
    parcela = db.get(ParcelaReceber, parcela_id)
    if parcela is None:
        raise NaoEncontrado("Parcela não encontrada")
    return list(db.scalars(select(HistoricoParcela).where(HistoricoParcela.parcela_id == parcela_id)
                           .order_by(HistoricoParcela.data_hora.desc(), HistoricoParcela.id.desc())))


def bloquear_clientes(db: Session, usuario_id: int, empresa_id: int, cliente_ids: list[int], bloquear: bool) -> int:
    """Bloqueia (ou libera) os clientes das parcelas selecionadas, de uma vez: o bloqueio por atraso é à mão.
    Cada mudança fica nas anotações do cliente. Devolve quantos mudaram."""
    mudaram = 0
    for cliente_id in set(cliente_ids):
        cliente = db.get(Cliente, cliente_id)
        if cliente is None:
            raise NaoEncontrado("Cliente não encontrado")
        if cliente.bloqueado != bloquear:
            cliente.bloqueado = bloquear
            db.add(AnotacaoCliente(cliente_id=cliente.id, usuario_id=usuario_id, empresa_id=empresa_id,
                                   texto="Bloqueado pela cobrança (contas a receber)" if bloquear
                                   else "Liberado pela cobrança (contas a receber)"))
            mudaram += 1
    db.commit()
    return mudaram


def cancelar_conta(db: Session, conta: ContaReceber, usuario_id: int, motivo: str) -> None:
    """A venda foi cancelada: o carnê deixa de ser devido. Quem chama confere que nenhuma parcela foi paga."""
    conta.cancelada_em = datetime.now()
    for parcela in conta.parcelas:
        if parcela.aberto:
            _historico(db, parcela, "cancelamento", f"falta {moeda(parcela.aberto)}", "venda cancelada", motivo,
                       usuario_id)
            parcela.aberto = ZERO


def teve_pagamento(db: Session, conta: ContaReceber) -> bool:
    """Alguma parcela do carnê já foi paga (toda ou em parte); o recebimento estornado não conta."""
    if any(p.aberto < p.valor for p in conta.parcelas):
        return True
    ids = [p.id for p in conta.parcelas]
    return bool(ids) and db.scalar(select(func.count()).select_from(ItemRecebimento).join(RecebimentoCrediario)
                                   .where(ItemRecebimento.parcela_id.in_(ids),
                                          RecebimentoCrediario.estornado_em.is_(None))) > 0
