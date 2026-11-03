"""Regras da venda (D26).

O vendedor abre a venda, inclui os itens, escolhe a forma de pagamento, dá o
desconto e fecha a venda com o cliente; o caixa recebe a venda fechada. O
desconto fica em cada item: o da forma e o dado no total são rateados entre os
itens, menos os em queima, que não têm desconto. Desconto acima do limite do
perfil, e parcelas acima do limite da forma, pedem o login e a senha de quem
pode autorizar, que fica registrado na venda.

As funções que mudam a venda conferem a autorização antes de mexer em
qualquer coisa: a senha errada conta tentativa e grava na hora.
"""
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.dominios.acesso import servico as acesso
from app.dominios.acesso.modelos import Usuario
from app.dominios.caixa import servico as caixa
from app.dominios.caixa.modelos import ABERTO, FormaPagamento, LancamentoCaixa
from app.dominios.cidades.modelos import Cidade
from app.dominios.clientes import repositorio as repo_clientes
from app.dominios.clientes.modelos import Cliente
from app.dominios.estoque import repositorio as repo_estoque
from app.dominios.estoque import servico as estoque
from app.dominios.produtos.modelos import Produto
from app.dominios.receber import servico as contas
from app.dominios.receber.modelos import ContaReceber
from app.dominios.vendas.esquemas import (
    Autorizacao, ConsumidorDados, EntregaDados, ItemAlteracao, ItemNovo, PedidoDesconto, PedidoForma, PedidoRecebimento,
    VendaDados,
)
from app.dominios.vendas.modelos import (
    ABERTA, CANCELADA, DESCARTADA, DIAS_PARA_CANCELAR, DIAS_PARA_VENCER, FECHADA, RECEBIDA, SITUACOES, VENCIDA, Consumidor, EntregaVenda, ItemVenda,
    PagamentoVenda, Venda,
)
from app.nucleo.textos import moeda

ZERO = Decimal("0.00")
CENTAVO = Decimal("0.01")
CEM = Decimal(100)
PERMISSAO_PARCELAS = "vendas.autorizar"  # também o crediário acima do limite do cliente


class ErroVenda(Exception):
    """Erro de regra da venda; a mensagem vai para o usuário."""


class NaoEncontrado(ErroVenda):
    pass


class DadoInvalido(ErroVenda):
    pass


class PedeAutorizacao(ErroVenda):
    """Passou do limite: a tela pede o login e a senha de quem autoriza e manda de novo."""


def _centavos(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _percentual(valor: Decimal) -> str:
    return f"{valor.quantize(CENTAVO, rounding=ROUND_HALF_UP).normalize():f}".replace(".", ",") + "%"


def _tem_fracao(valor: Decimal) -> bool:
    return valor != valor.to_integral_value()


def documento(venda: Venda) -> str:
    return f"venda {venda.numero}"


# ------------------------------------------------------------ consultar

def vencer_abertas(db: Session, empresa_id: int) -> None:
    """A venda aberta ou fechada há mais de 10 dias vence e não pode mais ser recebida."""
    db.execute(update(Venda).where(Venda.empresa_id == empresa_id, Venda.situacao.in_([ABERTA, FECHADA]),
                                   Venda.vence_em < datetime.now()).values(situacao=VENCIDA))
    db.commit()


def listar(db: Session, empresa_id: int, situacao: str | None, busca: str | None, vendedor_id: int | None,
           limite: int, deslocamento: int) -> tuple[list[Venda], int]:
    vencer_abertas(db, empresa_id)
    filtros = [Venda.empresa_id == empresa_id]
    if situacao:
        filtros.append(Venda.situacao == situacao)
    if vendedor_id:
        filtros.append(Venda.vendedor_id == vendedor_id)
    if busca and busca.strip():
        termo = busca.strip()
        if termo.isdigit():
            filtros.append(Venda.numero == int(termo))
        else:
            filtros.append(Venda.comprador.ilike(f"%{termo}%"))
    total = db.scalar(select(func.count()).select_from(Venda).where(*filtros))
    itens = db.scalars(select(Venda).where(*filtros).order_by(Venda.id.desc()).limit(limite).offset(deslocamento))
    return list(itens), total


def obter(db: Session, empresa_id: int, venda_id: int) -> Venda:
    venda = db.get(Venda, venda_id)
    if venda is None or venda.empresa_id != empresa_id:
        raise NaoEncontrado("Venda não encontrada")
    if venda.situacao in (ABERTA, FECHADA) and venda.vence_em < datetime.now():
        venda.situacao = VENCIDA
        db.commit()
    return venda


def _salvar(db: Session, venda: Venda) -> Venda:
    """Grava e faz a venda e os itens serem lidos de novo do banco (com as casas decimais de lá)."""
    db.commit()
    db.expire_all()
    return venda


def _na_situacao(db: Session, empresa_id: int, venda_id: int, *situacoes: str) -> Venda:
    venda = obter(db, empresa_id, venda_id)
    if venda.situacao not in situacoes:
        if venda.situacao == FECHADA:
            raise DadoInvalido("Esta venda está fechada; reabra para mudar")
        if venda.situacao == ABERTA:
            raise DadoInvalido("O vendedor ainda não fechou esta venda")
        raise DadoInvalido(f"Esta venda está {SITUACOES[venda.situacao].lower()}")
    return venda


def _aberta(db: Session, empresa_id: int, venda_id: int) -> Venda:
    return _na_situacao(db, empresa_id, venda_id, ABERTA)


# ------------------------------------------------------------ montar

def criar(db: Session, empresa_id: int, usuario_id: int) -> Venda:
    numero = (db.scalar(select(func.max(Venda.numero)).where(Venda.empresa_id == empresa_id)) or 0) + 1
    venda = Venda(empresa_id=empresa_id, numero=numero, situacao=ABERTA, vendedor_id=usuario_id,
                  vence_em=datetime.now() + timedelta(days=DIAS_PARA_VENCER), parcelas=1,
                  percentual_desconto=Decimal(0), subtotal=ZERO, desconto=ZERO, total=ZERO)
    db.add(venda)
    db.commit()
    db.refresh(venda)
    return venda


def _autorizador(db: Session, autorizacao: Autorizacao | None) -> Usuario | None:
    if autorizacao is None:
        return None
    try:
        return acesso.autenticar(db, autorizacao.login, autorizacao.senha)
    except acesso.UsuarioBloqueado:
        raise DadoInvalido("O login de quem autoriza está bloqueado por tentativas erradas; espere um pouco")
    except acesso.ErroAcesso:
        raise DadoInvalido("Login ou senha de quem autoriza não confere")


def _com_desconto(venda: Venda) -> list[ItemVenda]:
    """Os itens que aceitam desconto: os em queima, não."""
    return [i for i in venda.itens if not i.em_queima]


def _base_do_desconto(venda: Venda) -> Decimal:
    return sum((i.bruto for i in _com_desconto(venda)), ZERO)


def _recalcular(venda: Venda) -> None:
    for item in venda.itens:
        item.total = item.bruto - item.desconto
    venda.subtotal = sum((i.bruto for i in venda.itens), ZERO)
    venda.desconto = sum((i.desconto for i in venda.itens), ZERO)
    venda.total = venda.subtotal - venda.desconto + venda.taxa_entrega


def _ratear(venda: Venda, valor: Decimal) -> None:
    """Divide o desconto entre os itens que aceitam desconto, na proporção do valor de cada um;
    os centavos que sobram vão no maior."""
    itens = _com_desconto(venda)
    base = _base_do_desconto(venda)
    if valor > base:
        raise DadoInvalido("O desconto passa do valor dos itens que aceitam desconto" if len(itens) < len(venda.itens)
                           else "O desconto passa do valor da venda")
    for item in venda.itens:
        item.desconto = ZERO
    if itens:
        maior = max(itens, key=lambda i: i.bruto)
        for item in itens:
            if item is not maior:
                item.desconto = _centavos(valor * item.bruto / base) if base else ZERO
        maior.desconto = valor - sum((i.desconto for i in itens if i is not maior), ZERO)
    _recalcular(venda)


def _aplicar_percentual(venda: Venda) -> None:
    _ratear(venda, _centavos(_base_do_desconto(venda) * venda.percentual_desconto / CEM))


def _conferir_desconto(db: Session, venda: Venda, usuario: Usuario, autorizador: Usuario | None) -> None:
    """O desconto vai até o maior entre o da forma, o limite de quem está vendendo e o de quem já autorizou."""
    base = _base_do_desconto(venda)
    if venda.desconto <= 0 or base <= 0:
        return

    def cabe(limite: Decimal) -> bool:
        # o arredondamento item a item pode passar um centavo por item
        return venda.desconto <= _centavos(base * limite / CEM) + CENTAVO * len(venda.itens)

    limites = [acesso.limite_de_desconto(db, usuario, venda.empresa_id)]
    if venda.forma_pagamento is not None:
        limites.append(venda.forma_pagamento.desconto)
    if venda.desconto_autorizado_por is not None:
        limites.append(acesso.limite_de_desconto(db, venda.desconto_autorizado_por, venda.empresa_id))
    if cabe(max(limites)):
        return
    percentual = _percentual(venda.desconto * CEM / base)
    if autorizador is None:
        raise PedeAutorizacao(f"O desconto de {percentual} passa do seu limite ({_percentual(max(limites))}). "
                              "Peça a autorização de quem pode dar mais.")
    limite = acesso.limite_de_desconto(db, autorizador, venda.empresa_id)
    if not cabe(limite):
        raise PedeAutorizacao(f"O desconto de {percentual} passa também do limite de {autorizador.nome} "
                              f"({_percentual(limite)})")
    venda.desconto_autorizado_por = autorizador


def _conferir_parcelas(db: Session, venda: Venda, permissoes: set[str], usuario: Usuario,
                       autorizador: Usuario | None) -> None:
    forma = venda.forma_pagamento
    if forma is None:
        venda.parcelas = 1
        return
    if venda.parcelas > forma.parcelas:
        raise DadoInvalido(f"{forma.nome} vai até {forma.parcelas}x")
    if venda.parcelas <= forma.parcelas_sem_autorizacao or venda.parcelas_autorizadas_por is not None:
        return
    venda.parcelas_autorizadas_por = _quem_autoriza_parcelas(db, venda, forma, permissoes, usuario, autorizador)


def _quem_autoriza_parcelas(db: Session, venda: Venda, forma: FormaPagamento, permissoes: set[str], usuario: Usuario,
                            autorizador: Usuario | None) -> Usuario:
    """Parcelas acima do limite sem autorização da forma: quem está vendendo pode, se tiver vendas.autorizar;
    senão, pede o login e a senha de quem tem."""
    if PERMISSAO_PARCELAS in permissoes:
        return usuario
    if autorizador is None:
        raise PedeAutorizacao(f"{forma.nome} acima de {forma.parcelas_sem_autorizacao}x pede a autorização da gerência")
    if PERMISSAO_PARCELAS not in acesso.permissoes_na_empresa(db, autorizador, venda.empresa_id):
        raise PedeAutorizacao(f"{autorizador.nome} não pode autorizar parcelas acima do limite")
    return autorizador


def _aplicar_consumidor(db: Session, venda: Venda, dados: ConsumidorDados | None) -> None:
    """Quem compra sem cadastro. Com CPF, telefone, e-mail ou aniversário, vira (ou atualiza) o cadastro curto do
    consumidor; o CPF acha quem já comprou antes. Só com o nome, fica só na venda."""
    venda.comprador = dados.nome if dados else None
    if dados is None or not (dados.cpf or dados.telefone or dados.email or dados.dia_nascimento):
        venda.consumidor = None
        return
    if not dados.nome:
        raise DadoInvalido("Informe o nome de quem está comprando")
    atual = venda.consumidor
    registro = db.scalar(select(Consumidor).where(Consumidor.cpf == dados.cpf)) if dados.cpf else None
    if registro is None and atual is not None and atual.cpf in (None, dados.cpf):
        registro = atual
    if registro is None:
        registro = Consumidor()
        db.add(registro)
    registro.nome = dados.nome
    # o que não foi dado agora continua como estava (veio da compra anterior)
    for campo in ("cpf", "dia_nascimento", "mes_nascimento", "telefone", "email"):
        if getattr(dados, campo) is not None:
            setattr(registro, campo, getattr(dados, campo))
    venda.consumidor = registro


def _aplicar_entrega(db: Session, venda: Venda, dados: EntregaDados | None) -> None:
    if dados is None:
        venda.entrega = None
        return
    if dados.cidade_id is not None and db.get(Cidade, dados.cidade_id) is None:
        raise NaoEncontrado("Cidade não encontrada")
    entrega = venda.entrega or EntregaVenda()
    for campo, valor in dados.model_dump().items():
        setattr(entrega, campo, valor)
    entrega.cidade = db.get(Cidade, dados.cidade_id) if dados.cidade_id else None
    venda.entrega = entrega


def alterar(db: Session, empresa_id: int, usuario: Usuario, permissoes: set[str], venda_id: int,
            dados: VendaDados) -> Venda:
    """Cliente (ou consumidor), forma de pagamento, parcelas, entrega e observação.
    Trocar a forma aplica o desconto dela a todos os itens."""
    autorizador = _autorizador(db, dados.autorizacao)
    venda = _aberta(db, empresa_id, venda_id)
    if dados.cliente_id is not None:
        cliente = db.get(Cliente, dados.cliente_id)
        if cliente is None:
            raise NaoEncontrado("Cliente não encontrado")
        venda.cliente = cliente
        venda.consumidor = None
        venda.comprador = cliente.nome
    else:
        venda.cliente = None
        _aplicar_consumidor(db, venda, dados.consumidor)
    _aplicar_entrega(db, venda, dados.entrega)
    if dados.forma_pagamento_id != venda.forma_pagamento_id:
        forma = None
        if dados.forma_pagamento_id is not None:
            forma = db.get(FormaPagamento, dados.forma_pagamento_id)
            if forma is None or not forma.ativo:
                raise DadoInvalido("Forma de pagamento não encontrada")
        venda.forma_pagamento = forma
        venda.percentual_desconto = forma.desconto if forma else Decimal(0)
        venda.desconto_autorizado_por = None
        venda.parcelas_autorizadas_por = None
        _aplicar_percentual(venda)
    venda.parcelas = dados.parcelas
    venda.observacao = dados.observacao
    _recalcular(venda)
    _conferir_desconto(db, venda, usuario, autorizador)
    _conferir_parcelas(db, venda, permissoes, usuario, autorizador)
    return _salvar(db, venda)


def incluir_item(db: Session, empresa_id: int, usuario: Usuario, venda_id: int, dados: ItemNovo) -> Venda:
    """O mesmo produto de novo soma na linha que já existe. O item novo leva o % de desconto da venda."""
    autorizador = _autorizador(db, dados.autorizacao)
    venda = _aberta(db, empresa_id, venda_id)
    produto = db.get(Produto, dados.produto_id)
    if produto is None:
        raise NaoEncontrado("Produto não encontrado")
    item = next((i for i in venda.itens if i.produto_id == produto.id), None)
    quantidade = dados.quantidade + (item.quantidade if item else 0)
    if not produto.fracionado and _tem_fracao(quantidade):
        raise DadoInvalido(f"{produto.nome} não aceita quantidade com fração")
    if item is None:
        item = ItemVenda(ordem=max((i.ordem for i in venda.itens), default=0) + 1, produto=produto,
                         descricao=produto.nome, quantidade=quantidade, em_queima=bool(produto.preco_queima),
                         preco=produto.preco_queima or produto.preco_venda, desconto=ZERO)
        venda.itens.append(item)
        if not item.em_queima:
            item.desconto = _centavos(item.bruto * venda.percentual_desconto / CEM)
    else:
        antes = item.bruto
        item.quantidade = quantidade
        item.desconto = _centavos(item.desconto * item.bruto / antes) if antes else ZERO
    _recalcular(venda)
    _conferir_desconto(db, venda, usuario, autorizador)
    return _salvar(db, venda)


def _item(venda: Venda, item_id: int) -> ItemVenda:
    item = next((i for i in venda.itens if i.id == item_id), None)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    return item


def alterar_item(db: Session, empresa_id: int, usuario: Usuario, venda_id: int, item_id: int,
                 dados: ItemAlteracao) -> Venda:
    autorizador = _autorizador(db, dados.autorizacao)
    venda = _aberta(db, empresa_id, venda_id)
    item = _item(venda, item_id)
    if not item.produto.fracionado and _tem_fracao(dados.quantidade):
        raise DadoInvalido(f"{item.descricao} não aceita quantidade com fração")
    item.quantidade = dados.quantidade
    if dados.desconto > 0 and item.em_queima:
        raise DadoInvalido(f"{item.descricao} está em queima e não tem desconto")
    if dados.desconto > item.bruto:
        raise DadoInvalido("O desconto passa do valor do item")
    item.desconto = dados.desconto
    _recalcular(venda)
    _conferir_desconto(db, venda, usuario, autorizador)
    return _salvar(db, venda)


def excluir_item(db: Session, empresa_id: int, venda_id: int, item_id: int) -> Venda:
    venda = _aberta(db, empresa_id, venda_id)
    venda.itens.remove(_item(venda, item_id))
    _recalcular(venda)
    return _salvar(db, venda)


def dar_desconto(db: Session, empresa_id: int, usuario: Usuario, venda_id: int, pedido: PedidoDesconto) -> Venda:
    """Desconto no total, rateado entre os itens (substitui o que cada item tinha)."""
    autorizador = _autorizador(db, pedido.autorizacao)
    venda = _aberta(db, empresa_id, venda_id)
    if not venda.itens:
        raise DadoInvalido("Inclua os itens antes de dar o desconto")
    base = _base_do_desconto(venda)
    if not base:
        raise DadoInvalido("Os itens desta venda estão em queima e não têm desconto")
    valor = pedido.valor if pedido.valor is not None else _centavos(base * pedido.percentual / CEM)
    _ratear(venda, valor)
    venda.percentual_desconto = (valor * CEM / base).quantize(Decimal("0.0001"))
    _conferir_desconto(db, venda, usuario, autorizador)
    return _salvar(db, venda)


def fechar(db: Session, empresa_id: int, venda_id: int) -> Venda:
    """O vendedor fecha a venda com o cliente; daí ela vai para o caixa, que acha pelo nome de quem comprou."""
    venda = _aberta(db, empresa_id, venda_id)
    if not venda.itens:
        raise DadoInvalido("A venda não tem itens")
    forma = venda.forma_pagamento
    if forma is None:
        raise DadoInvalido("Escolha a forma de pagamento")
    if not forma.ativo:
        raise DadoInvalido(f"A forma {forma.nome} está desativada; escolha outra")
    if venda.cliente is not None:
        venda.comprador = venda.cliente.nome
    elif forma.tipo == "crediario":
        raise DadoInvalido("O crediário pede o cliente cadastrado")
    if not venda.comprador:
        raise DadoInvalido("Informe o nome de quem está comprando")
    entrega = venda.entrega
    if entrega is not None and not (entrega.logradouro and entrega.numero and entrega.bairro and entrega.cidade_id):
        raise DadoInvalido("Falta o endereço da entrega: rua, número, bairro e cidade")
    venda.situacao = FECHADA
    venda.fechada_em = datetime.now()
    return _salvar(db, venda)


def reabrir(db: Session, empresa_id: int, venda_id: int) -> Venda:
    """Só a venda fechada volta para o vendedor mudar ou incluir mais coisas (o cliente mudou de ideia no caixa...)."""
    venda = _na_situacao(db, empresa_id, venda_id, FECHADA)
    venda.situacao = ABERTA
    venda.fechada_em = None
    return _salvar(db, venda)


def buscar_cpf(db: Session, cpf: str) -> tuple[Cliente | None, Consumidor | None]:
    """Quem tem este CPF: cliente cadastrado ou consumidor que já comprou."""
    return (repo_clientes.cliente_por_documento(db, cpf),
            db.scalar(select(Consumidor).where(Consumidor.cpf == cpf)))


def descartar(db: Session, empresa_id: int, usuario_id: int, venda_id: int, motivo: str) -> Venda:
    """A venda aberta ou fechada em que o cliente desistiu: não gerou nada (caixa, estoque, carnê, nota), então só
    fica marcada, com quem, quando e por quê. Não se apaga: a numeração fica sem buraco e o descarte fica à vista.
    O cancelamento, que desfaz tudo, é só da venda efetivada (cancelar_recebida)."""
    venda = _na_situacao(db, empresa_id, venda_id, ABERTA, FECHADA)
    venda.situacao = DESCARTADA
    venda.cancelada_em = datetime.now()
    venda.cancelada_por_id = usuario_id
    venda.motivo_cancelamento = motivo
    return _salvar(db, venda)


def cancelar_recebida(db: Session, empresa_id: int, usuario_id: int, venda_id: int, motivo: str,
                      sessao_caixa_id: int | None) -> Venda:
    """Cancela a venda já recebida e o que veio dela: o caixa, o estoque e o carnê. Só nos primeiros dias, e só se
    nenhuma parcela do carnê foi paga. A NFC-e é cancelada pelo usuário, à parte.

    O caixa: se o do recebimento ainda está aberto, os lançamentos da venda são estornados; se já fechou, sai o
    mesmo valor, em cada forma, pelo caixa aberto informado (o do computador)."""
    venda = obter(db, empresa_id, venda_id)
    if venda.situacao in (ABERTA, FECHADA):
        raise DadoInvalido("Esta venda não foi efetivada: em vez de cancelar, descarte")
    if venda.situacao != RECEBIDA:
        raise DadoInvalido(f"Esta venda está {SITUACOES[venda.situacao].lower()}")
    if venda.recebida_em < datetime.now() - timedelta(days=DIAS_PARA_CANCELAR):
        raise DadoInvalido(f"A venda foi recebida há mais de {DIAS_PARA_CANCELAR} dias e não pode mais ser cancelada")
    conta = contas.conta_da_venda(db, venda.id)
    if conta is not None and contas.teve_pagamento(db, conta):
        raise DadoInvalido("Esta venda já teve parcela do carnê recebida e não pode ser cancelada")

    original = venda.sessao_caixa
    lancamentos = [x for x in original.lancamentos if x.documento == documento(venda) and x.estornado_em is None]
    agora = datetime.now()
    if original.situacao == ABERTO:
        for lancamento in lancamentos:
            lancamento.estornado_em, lancamento.estornado_por_id = agora, usuario_id
    else:
        if sessao_caixa_id is None:
            raise DadoInvalido(f"O {original.caixa.nome} do recebimento já foi fechado: "
                               "informe o caixa aberto por onde o dinheiro sai")
        try:
            sessao = caixa.obter_sessao(db, empresa_id, sessao_caixa_id)
        except caixa.ErroCaixa as e:
            raise NaoEncontrado(str(e))
        if sessao.situacao != ABERTO:
            raise DadoInvalido(f"O caixa {sessao.caixa.nome} está fechado")
        for lancamento in lancamentos:
            db.add(LancamentoCaixa(sessao_id=sessao.id, tipo="saida", motivo="cancelamento_venda",
                                   forma_pagamento_id=lancamento.forma_pagamento_id, valor=lancamento.valor,
                                   documento=documento(venda), usuario_id=usuario_id, historico=motivo[:80]))
    for item in venda.itens:
        try:
            estoque.movimentar(db, empresa_id, item.produto_id, "cancelamento_venda", item.quantidade,
                               usuario_id=usuario_id, documento=documento(venda))
        except estoque.ErroEstoque as e:
            raise DadoInvalido(str(e))
    if conta is not None:
        contas.cancelar_conta(db, conta, usuario_id, motivo)
    venda.situacao = CANCELADA
    venda.cancelada_em = agora
    venda.cancelada_por_id = usuario_id
    venda.motivo_cancelamento = motivo
    return _salvar(db, venda)


# ------------------------------------------------------------ receber

def _conferir_limite(db: Session, venda: Venda, a_prazo: Decimal, permissoes: set[str], usuario: Usuario,
                     autorizador: Usuario | None) -> None:
    """O crediário vai até o limite disponível do cliente (o limite menos o que está em aberto em todas as lojas);
    acima, pede a gerência."""
    credito = contas.credito(db, venda.cliente)
    if credito.impedimento:
        raise DadoInvalido(credito.impedimento)
    if a_prazo <= credito.disponivel:
        return
    mensagem = (f"O crediário de {moeda(a_prazo)} passa do limite disponível do cliente "
                f"({moeda(max(credito.disponivel, ZERO))})")
    if PERMISSAO_PARCELAS in permissoes:
        venda.limite_autorizado_por = usuario
        return
    if autorizador is None:
        raise PedeAutorizacao(f"{mensagem}. Peça a autorização da gerência.")
    if PERMISSAO_PARCELAS not in acesso.permissoes_na_empresa(db, autorizador, venda.empresa_id):
        raise PedeAutorizacao(f"{autorizador.nome} não pode autorizar o crediário acima do limite")
    venda.limite_autorizado_por = autorizador


def _forma_ativa(db: Session, forma_id: int) -> FormaPagamento:
    forma = db.get(FormaPagamento, forma_id)
    if forma is None:
        raise NaoEncontrado("Forma de pagamento não encontrada")
    if not forma.ativo:
        raise DadoInvalido(f"A forma {forma.nome} está desativada; escolha outra")
    return forma


def trocar_forma(db: Session, empresa_id: int, usuario: Usuario, permissoes: set[str], venda_id: int,
                 pedido: PedidoForma) -> Venda:
    """No caixa, o cliente muda a forma de pagamento da venda fechada (era crédito, vai no débito...).

    Se o desconto da forma nova é outro, ele vale para todos os itens e o que tinha sido dado cai, como no
    VB6; se é o mesmo, o desconto da venda fica como estava.
    """
    autorizador = _autorizador(db, pedido.autorizacao)
    venda = _na_situacao(db, empresa_id, venda_id, FECHADA)
    forma = _forma_ativa(db, pedido.forma_pagamento_id)
    if forma.tipo == "crediario" and venda.cliente is None:
        raise DadoInvalido("O crediário pede o cliente cadastrado; reabra a venda para o vendedor escolher o cliente")
    antiga = venda.forma_pagamento
    venda.forma_pagamento = forma
    if antiga is None or antiga.desconto != forma.desconto:
        venda.percentual_desconto = forma.desconto
        venda.desconto_autorizado_por = None
        _aplicar_percentual(venda)
    if antiga is not forma or venda.parcelas != pedido.parcelas:
        venda.parcelas_autorizadas_por = None
    venda.parcelas = pedido.parcelas
    _conferir_parcelas(db, venda, permissoes, usuario, autorizador)
    return _salvar(db, venda)


def _pagamentos(db: Session, venda: Venda, pedido: PedidoRecebimento, permissoes: set[str], usuario: Usuario,
                autorizador: Usuario | None) -> list[PagamentoVenda]:
    pagamentos = []
    for ordem, dados in enumerate(pedido.pagamentos, start=1):
        forma = _forma_ativa(db, dados.forma_pagamento_id)
        if forma.tipo == "crediario":
            raise DadoInvalido("O crediário não entra como pagamento à vista; escolha o crediário como forma da venda")
        if dados.parcelas > forma.parcelas:
            raise DadoInvalido(f"{forma.nome} vai até {forma.parcelas}x")
        if dados.parcelas > forma.parcelas_sem_autorizacao and venda.parcelas_autorizadas_por is None:
            venda.parcelas_autorizadas_por = _quem_autoriza_parcelas(db, venda, forma, permissoes, usuario, autorizador)
        pagamentos.append(PagamentoVenda(ordem=ordem, forma_pagamento=forma, valor=dados.valor,
                                         parcelas=dados.parcelas))
    return pagamentos


def receber(db: Session, empresa_id: int, usuario: Usuario, permissoes: set[str], venda_id: int,
            pedido: PedidoRecebimento) -> tuple[Venda, list[str]]:
    """O caixa recebe a venda fechada: lança no caixa e baixa o estoque. Devolve a venda e os avisos de estoque negativo.

    O cliente paga em uma ou mais formas (um pouco no PIX, um pouco no cartão). No crediário, o que ele paga
    agora é a entrada, e o resto vira o carnê, em parcelas iguais e sem juros, contadas da data base.
    """
    autorizador = _autorizador(db, pedido.autorizacao)
    venda = _na_situacao(db, empresa_id, venda_id, FECHADA)
    forma = venda.forma_pagamento
    if forma is None:
        raise DadoInvalido("Escolha a forma de pagamento")
    if not forma.ativo:
        raise DadoInvalido(f"A forma {forma.nome} está desativada; escolha outra")
    try:
        sessao = caixa.obter_sessao(db, empresa_id, pedido.sessao_caixa_id)
    except caixa.ErroCaixa as e:
        raise NaoEncontrado(str(e))
    if sessao.situacao != ABERTO:
        raise DadoInvalido(f"O caixa {sessao.caixa.nome} está fechado")
    if pedido.modelo_nota == "55" and (venda.cliente is None or not venda.cliente.cpf_cnpj):
        raise DadoInvalido("A NF-e (modelo 55) pede o cliente cadastrado, com CPF ou CNPJ")

    pagamentos = _pagamentos(db, venda, pedido, permissoes, usuario, autorizador)
    pago = sum((p.valor for p in pagamentos), ZERO)
    venda.limite_autorizado_por = None
    venda.data_base = None
    lancamentos = []
    if forma.tipo == "crediario":
        if venda.cliente is None:
            raise DadoInvalido("O crediário pede o cliente cadastrado")
        if pago >= venda.total:
            raise DadoInvalido("A entrada cobre a venda toda; troque a forma da venda")
        a_prazo = venda.total - pago
        base = pedido.data_base or date.today()
        if base < contas.somar_meses(date.today(), -1):
            raise DadoInvalido("A data base não pode ser de mais de um mês atrás")
        _conferir_limite(db, venda, a_prazo, permissoes, usuario, autorizador)
        venda.data_base = base
        primeiro = contas.vencimentos(base, 2, forma.intervalo)[1]
        contas.lancar_carne(db, empresa_id, venda.cliente_id, venda.id, a_prazo, venda.parcelas, primeiro,
                             forma.intervalo, f"Venda {venda.numero} {venda.cliente.nome}", usuario.id,
                             pedido.tipo_cobranca or contas.tipo_cobranca_do_cliente(venda.cliente))
        lancamentos.append((forma, a_prazo))
    elif pago < venda.total:
        raise DadoInvalido(f"Falta lançar {moeda(venda.total - pago)}")
    elif pago > venda.total:
        raise DadoInvalido(f"O lançado passa do total em {moeda(pago - venda.total)}; "
                           "o troco sai do valor que o cliente deu no dinheiro")

    no_dinheiro = sum((p.valor for p in pagamentos if p.forma_pagamento.tipo == "dinheiro"), ZERO)
    venda.valor_recebido = None
    if no_dinheiro:
        venda.valor_recebido = pedido.valor_recebido or no_dinheiro
        if venda.valor_recebido < no_dinheiro:
            raise DadoInvalido(f"O valor que o cliente deu é menor que os {moeda(no_dinheiro)} no dinheiro")
    venda.pagamentos = pagamentos
    venda.modelo_nota = pedido.modelo_nota
    for forma_lancada, valor in [(p.forma_pagamento, p.valor) for p in pagamentos] + lancamentos:
        db.add(LancamentoCaixa(sessao_id=sessao.id, tipo="entrada", motivo="venda",
                               forma_pagamento_id=forma_lancada.id, valor=valor, documento=documento(venda),
                               usuario_id=usuario.id))
    avisos = []
    for item in venda.itens:
        try:
            movimento = estoque.movimentar(db, empresa_id, item.produto_id, "venda", -item.quantidade,
                                           usuario_id=usuario.id, documento=documento(venda))
        except estoque.ErroEstoque as e:
            raise DadoInvalido(str(e))
        if movimento.saldo < 0:
            avisos.append(f"{item.descricao}: o estoque da loja ficou em {movimento.saldo.normalize():f}")
    venda.situacao = RECEBIDA
    venda.sessao_caixa_id = sessao.id
    venda.recebida_em = datetime.now()
    venda.recebida_por_id = usuario.id
    return _salvar(db, venda), avisos


def credito(db: Session, venda: Venda) -> contas.Credito | None:
    """O crédito do cliente, para a tela mostrar enquanto a venda no crediário não foi recebida."""
    if venda.situacao not in (ABERTA, FECHADA) or venda.cliente is None or venda.forma_pagamento is None:
        return None
    if venda.forma_pagamento.tipo != "crediario":
        return None
    return contas.credito(db, venda.cliente)


def carne(db: Session, venda: Venda) -> ContaReceber | None:
    return contas.conta_da_venda(db, venda.id)


def disponiveis(db: Session, venda: Venda) -> dict[int, Decimal]:
    """O estoque da loja de cada produto da venda (o que não tem linha fica de fora: zero)."""
    return repo_estoque.quantidades(db, venda.empresa_id, [i.produto_id for i in venda.itens])

