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
from app.dominios.clientes.modelos import Cliente
from app.dominios.receber.esquemas import RecebimentoDados
from app.dominios.receber.modelos import (
    ContaReceber, ItemRecebimento, PagamentoRecebimento, ParcelaReceber, RecebimentoCrediario,
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
    em_aberto: Decimal  # parcelas em aberto em todas as lojas
    disponivel: Decimal
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


def credito(db: Session, cliente: Cliente) -> Credito:
    """O limite restante é o limite do cliente menos tudo o que ele tem em aberto, em qualquer loja."""
    aberto = em_aberto(db, cliente.id)
    return Credito(limite=cliente.limite_credito, em_aberto=aberto, disponivel=cliente.limite_credito - aberto,
                   bloqueado=cliente.bloqueado, suspenso=cliente.credito_suspenso)


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


def lancar_carne(db: Session, empresa_id: int, cliente_id: int, venda_id: int | None, valor: Decimal,
                 parcelas: int, primeiro_vencimento: date, intervalo: int, historico: str,
                 usuario_id: int) -> ContaReceber:
    """Cria a conta e as parcelas; quem chama grava."""
    conta = ContaReceber(empresa_id=empresa_id, cliente_id=cliente_id, venda_id=venda_id, valor=valor,
                         historico=historico[:80], usuario_id=usuario_id)
    datas = vencimentos(primeiro_vencimento, parcelas, intervalo)
    for numero, (vencimento, parte) in enumerate(zip(datas, dividir(valor, parcelas)), start=1):
        conta.parcelas.append(ParcelaReceber(numero=numero, vencimento=vencimento, valor=parte, aberto=parte))
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
