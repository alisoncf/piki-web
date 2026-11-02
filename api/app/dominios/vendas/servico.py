"""Regras da venda (D26).

O vendedor abre a venda, inclui os itens, escolhe a forma de pagamento e dá o
desconto; o caixa recebe. O desconto fica em cada item: o da forma e o dado no
total são rateados entre os itens. Desconto acima do limite do perfil, e
parcelas acima do limite da forma, pedem o login e a senha de quem pode
autorizar, que fica registrado na venda.

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
from app.dominios.clientes.modelos import Cliente
from app.dominios.estoque import repositorio as repo_estoque
from app.dominios.estoque import servico as estoque
from app.dominios.produtos.modelos import Produto
from app.dominios.receber import servico as contas
from app.dominios.receber.modelos import ContaReceber
from app.dominios.vendas.esquemas import Autorizacao, ItemAlteracao, ItemNovo, PedidoDesconto, PedidoRecebimento, VendaDados
from app.dominios.vendas.modelos import (
    ABERTA, CANCELADA, DIAS_PARA_VENCER, RECEBIDA, SITUACOES, VENCIDA, ItemVenda, Venda,
)

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
    """A venda aberta há mais de 10 dias vence e não pode mais ser recebida."""
    db.execute(update(Venda).where(Venda.empresa_id == empresa_id, Venda.situacao == ABERTA,
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
            filtros.append(Venda.cliente_id.in_(select(Cliente.id).where(Cliente.nome.ilike(f"%{termo}%"))))
    total = db.scalar(select(func.count()).select_from(Venda).where(*filtros))
    itens = db.scalars(select(Venda).where(*filtros).order_by(Venda.id.desc()).limit(limite).offset(deslocamento))
    return list(itens), total


def obter(db: Session, empresa_id: int, venda_id: int) -> Venda:
    venda = db.get(Venda, venda_id)
    if venda is None or venda.empresa_id != empresa_id:
        raise NaoEncontrado("Venda não encontrada")
    if venda.situacao == ABERTA and venda.vence_em < datetime.now():
        venda.situacao = VENCIDA
        db.commit()
    return venda


def _salvar(db: Session, venda: Venda) -> Venda:
    """Grava e faz a venda e os itens serem lidos de novo do banco (com as casas decimais de lá)."""
    db.commit()
    db.expire_all()
    return venda


def _aberta(db: Session, empresa_id: int, venda_id: int) -> Venda:
    venda = obter(db, empresa_id, venda_id)
    if venda.situacao != ABERTA:
        raise DadoInvalido(f"Esta venda está {SITUACOES[venda.situacao].lower()}")
    return venda


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


def _recalcular(venda: Venda) -> None:
    for item in venda.itens:
        item.total = item.bruto - item.desconto
    venda.subtotal = sum((i.bruto for i in venda.itens), ZERO)
    venda.desconto = sum((i.desconto for i in venda.itens), ZERO)
    venda.total = venda.subtotal - venda.desconto


def _ratear(venda: Venda, valor: Decimal) -> None:
    """Divide o desconto entre os itens, na proporção do valor de cada um; os centavos que sobram vão no maior."""
    subtotal = sum((i.bruto for i in venda.itens), ZERO)
    if valor > subtotal:
        raise DadoInvalido("O desconto passa do valor da venda")
    if not venda.itens:
        return
    maior = max(venda.itens, key=lambda i: i.bruto)
    for item in venda.itens:
        if item is not maior:
            item.desconto = _centavos(valor * item.bruto / subtotal) if subtotal else ZERO
    maior.desconto = valor - sum((i.desconto for i in venda.itens if i is not maior), ZERO)
    _recalcular(venda)


def _aplicar_percentual(venda: Venda) -> None:
    subtotal = sum((i.bruto for i in venda.itens), ZERO)
    _ratear(venda, _centavos(subtotal * venda.percentual_desconto / CEM))


def _conferir_desconto(db: Session, venda: Venda, usuario: Usuario, autorizador: Usuario | None) -> None:
    """O desconto vai até o maior entre o da forma, o limite de quem está vendendo e o de quem já autorizou."""
    if venda.desconto <= 0 or venda.subtotal <= 0:
        return

    def cabe(limite: Decimal) -> bool:
        # o arredondamento item a item pode passar um centavo por item
        return venda.desconto <= _centavos(venda.subtotal * limite / CEM) + CENTAVO * len(venda.itens)

    limites = [acesso.limite_de_desconto(db, usuario, venda.empresa_id)]
    if venda.forma_pagamento is not None:
        limites.append(venda.forma_pagamento.desconto)
    if venda.desconto_autorizado_por is not None:
        limites.append(acesso.limite_de_desconto(db, venda.desconto_autorizado_por, venda.empresa_id))
    if cabe(max(limites)):
        return
    percentual = _percentual(venda.desconto * CEM / venda.subtotal)
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
    if PERMISSAO_PARCELAS in permissoes:
        venda.parcelas_autorizadas_por = usuario
        return
    if autorizador is None:
        raise PedeAutorizacao(f"{forma.nome} acima de {forma.parcelas_sem_autorizacao}x pede a autorização da gerência")
    if PERMISSAO_PARCELAS not in acesso.permissoes_na_empresa(db, autorizador, venda.empresa_id):
        raise PedeAutorizacao(f"{autorizador.nome} não pode autorizar parcelas acima do limite")
    venda.parcelas_autorizadas_por = autorizador


def alterar(db: Session, empresa_id: int, usuario: Usuario, permissoes: set[str], venda_id: int,
            dados: VendaDados) -> Venda:
    """Cliente, forma de pagamento, parcelas e observação. Trocar a forma aplica o desconto dela a todos os itens."""
    autorizador = _autorizador(db, dados.autorizacao)
    venda = _aberta(db, empresa_id, venda_id)
    if dados.cliente_id is not None and db.get(Cliente, dados.cliente_id) is None:
        raise NaoEncontrado("Cliente não encontrado")
    venda.cliente_id = dados.cliente_id
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
                         descricao=produto.nome, quantidade=quantidade,
                         preco=produto.preco_queima or produto.preco_venda, desconto=ZERO)
        venda.itens.append(item)
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
    subtotal = sum((i.bruto for i in venda.itens), ZERO)
    valor = pedido.valor if pedido.valor is not None else _centavos(subtotal * pedido.percentual / CEM)
    _ratear(venda, valor)
    venda.percentual_desconto = (valor * CEM / subtotal).quantize(Decimal("0.0001")) if subtotal else Decimal(0)
    _conferir_desconto(db, venda, usuario, autorizador)
    return _salvar(db, venda)


def cancelar(db: Session, empresa_id: int, usuario_id: int, venda_id: int, motivo: str) -> Venda:
    """Só a venda aberta; a recebida é desfeita pela devolução (etapa 5)."""
    venda = _aberta(db, empresa_id, venda_id)
    venda.situacao = CANCELADA
    venda.cancelada_em = datetime.now()
    venda.cancelada_por_id = usuario_id
    venda.motivo_cancelamento = motivo
    return _salvar(db, venda)


# ------------------------------------------------------------ receber

def _moeda(valor: Decimal) -> str:
    texto = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto}"


def _conferir_limite(db: Session, venda: Venda, a_prazo: Decimal, permissoes: set[str], usuario: Usuario,
                     autorizador: Usuario | None) -> None:
    """O crediário vai até o limite disponível do cliente (o limite menos o que está em aberto em todas as lojas);
    acima, pede a gerência."""
    credito = contas.credito(db, venda.cliente)
    if credito.impedimento:
        raise DadoInvalido(credito.impedimento)
    if a_prazo <= credito.disponivel:
        return
    mensagem = (f"O crediário de {_moeda(a_prazo)} passa do limite disponível do cliente "
                f"({_moeda(max(credito.disponivel, ZERO))})")
    if PERMISSAO_PARCELAS in permissoes:
        venda.limite_autorizado_por = usuario
        return
    if autorizador is None:
        raise PedeAutorizacao(f"{mensagem}. Peça a autorização da gerência.")
    if PERMISSAO_PARCELAS not in acesso.permissoes_na_empresa(db, autorizador, venda.empresa_id):
        raise PedeAutorizacao(f"{autorizador.nome} não pode autorizar o crediário acima do limite")
    venda.limite_autorizado_por = autorizador


def _forma_da_entrada(db: Session, venda: Venda, pedido: PedidoRecebimento) -> FormaPagamento | None:
    if pedido.entrada <= 0:
        return None
    if pedido.entrada >= venda.total:
        raise DadoInvalido("A entrada cobre a venda toda; troque a forma de pagamento")
    if pedido.forma_entrada_id is None:
        raise DadoInvalido("Escolha a forma de pagamento da entrada")
    forma = db.get(FormaPagamento, pedido.forma_entrada_id)
    if forma is None or not forma.ativo or forma.tipo == "crediario":
        raise DadoInvalido("Forma de pagamento da entrada não encontrada")
    return forma


def receber(db: Session, empresa_id: int, usuario: Usuario, permissoes: set[str], venda_id: int,
            pedido: PedidoRecebimento) -> tuple[Venda, list[str]]:
    """O caixa recebe: lança a entrada no caixa e baixa o estoque. Devolve a venda e os avisos de estoque negativo.

    No crediário, a entrada (se houver) entra no caixa na forma em que foi paga, e o resto vira o carnê,
    em parcelas iguais e sem juros.
    """
    autorizador = _autorizador(db, pedido.autorizacao)
    venda = _aberta(db, empresa_id, venda_id)
    if not venda.itens:
        raise DadoInvalido("A venda não tem itens")
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

    # o que entra no caixa agora: (forma, valor)
    lancamentos = [(forma, venda.total)]
    venda.entrada = None
    venda.forma_entrada = None
    venda.limite_autorizado_por = None
    forma_na_mao = forma
    if forma.tipo == "crediario":
        if venda.cliente is None:
            raise DadoInvalido("O crediário pede o cliente cadastrado")
        forma_entrada = _forma_da_entrada(db, venda, pedido)
        entrada = pedido.entrada if forma_entrada else ZERO
        a_prazo = venda.total - entrada
        primeiro = pedido.primeiro_vencimento or contas.vencimentos(date.today(), 2, forma.intervalo)[1]
        if primeiro < date.today():
            raise DadoInvalido("O primeiro vencimento não pode ser antes de hoje")
        _conferir_limite(db, venda, a_prazo, permissoes, usuario, autorizador)
        venda.entrada = entrada
        venda.forma_entrada = forma_entrada
        forma_na_mao = forma_entrada
        lancamentos = [(forma, a_prazo)] + ([(forma_entrada, entrada)] if forma_entrada else [])
        contas.lancar_carne(db, empresa_id, venda.cliente_id, venda.id, a_prazo, venda.parcelas, primeiro,
                             forma.intervalo, f"Venda {venda.numero} {venda.cliente.nome}", usuario.id)

    venda.valor_recebido = None
    if forma_na_mao is not None and forma_na_mao.tipo == "dinheiro":
        venda.valor_recebido = pedido.valor_recebido or venda.pago_na_hora
        if venda.valor_recebido < venda.pago_na_hora:
            raise DadoInvalido("O valor recebido é menor que o total da venda" if forma_na_mao is forma
                               else "O valor recebido é menor que a entrada")
    for forma_lancada, valor in lancamentos:
        if valor > 0:
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
    """O crédito do cliente, para a tela mostrar enquanto a venda no crediário está aberta."""
    if venda.situacao != ABERTA or venda.cliente is None or venda.forma_pagamento is None             or venda.forma_pagamento.tipo != "crediario":
        return None
    return contas.credito(db, venda.cliente)


def carne(db: Session, venda: Venda) -> ContaReceber | None:
    return contas.conta_da_venda(db, venda.id)


def disponiveis(db: Session, venda: Venda) -> dict[int, Decimal]:
    """O estoque da loja de cada produto da venda (o que não tem linha fica de fora: zero)."""
    return repo_estoque.quantidades(db, venda.empresa_id, [i.produto_id for i in venda.itens])

