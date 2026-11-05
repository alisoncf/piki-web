"""Regras da consignação (D30): o cadastro de representantes, a transferência, a devolução e o acerto."""
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.dominios.caixa import servico as caixa
from app.dominios.caixa.modelos import ABERTO, FormaPagamento, LancamentoCaixa
from app.dominios.clientes.modelos import Cliente
from app.dominios.consignacao.esquemas import AcertoDados, LimitesDados, PagamentoDados, RepresentanteDados
from app.dominios.acesso import servico as acesso
from app.dominios.acesso.modelos import Usuario
from app.dominios.consignacao.modelos import (
    A_PRAZO, A_VISTA, ABERTA, COMISSOES_ACERTO, COMISSOES_PADRAO, CONFIRMADA, PARA_CLIENTE, PARA_REPRESENTANTE, Acerto,
    ComissaoParcela, ComissaoRepresentante, Devolucao, ItemAcerto, ItemDevolucao, ItemTransferencia, PagamentoAcerto,
    Representante, Transferencia,
)
from app.dominios.estoque import servico as estoque
from app.dominios.produtos.modelos import Produto
from app.dominios.receber import servico as contas
from app.dominios.receber.modelos import TIPOS_COBRANCA, ContaReceber
from app.nucleo.documentos import cpf_valido, so_digitos
from app.nucleo.seguranca import conferir_hash, gerar_hash
from app.nucleo.textos import moeda

ZERO = Decimal("0.00")
ZERO3 = Decimal("0.000")


class ErroConsignacao(Exception):
    """Erro de regra da consignação; a mensagem vai para o usuário."""


class NaoEncontrado(ErroConsignacao):
    pass


class DadoInvalido(ErroConsignacao):
    pass


class Duplicado(ErroConsignacao):
    pass


def listar(db: Session, busca: str | None = None, so_ativos: bool = False, limite: int = 200) -> list[Representante]:
    consulta = select(Representante).join(Representante.cliente).order_by(Cliente.nome)
    if busca and busca.strip():
        termo = busca.strip()
        condicoes = [func.lower(Cliente.nome).like(f"%{termo.lower()}%")]
        digitos = so_digitos(termo)
        if len(digitos) >= 5:
            condicoes.append(Cliente.cpf_cnpj.like(f"%{digitos}%"))
        if termo.isdigit() and len(termo) <= 6:  # só números, curto: o código
            condicoes.append(Representante.codigo == int(termo))
        consulta = consulta.where(or_(*condicoes))
    if so_ativos:
        consulta = consulta.where(Representante.ativo.is_(True))
    return list(db.scalars(consulta.limit(limite)))


def obter(db: Session, representante_id: int) -> Representante:
    representante = db.get(Representante, representante_id)
    if representante is None:
        raise NaoEncontrado("Representante não encontrado")
    return representante


def comissoes(representante: Representante) -> list[dict]:
    """As comissões de todos os tipos de cobrança e dos acertos à vista e de queima: a do representante, ou a
    padrão."""
    proprias = {c.tipo_cobranca for c in representante.comissoes}
    nomes = {tipo: nome for tipo, (nome, _) in TIPOS_COBRANCA.items()} | {tipo: nome for tipo, (nome, _) in COMISSOES_ACERTO.items()}
    return [{"tipo_cobranca": tipo, "nome": nome, "percentual": representante.comissao(tipo), "padrao": tipo not in proprias,
             "percentual_padrao": COMISSOES_PADRAO[tipo]}
            for tipo, nome in nomes.items()]


def _aplicar(representante: Representante, dados: RepresentanteDados) -> None:
    if dados.avalista_cpf and not cpf_valido(dados.avalista_cpf):
        raise DadoInvalido("CPF do avalista inválido")
    for campo, valor in dados.model_dump().items():
        setattr(representante, campo, valor.strip() or None if isinstance(valor, str) else valor)


def criar(db: Session, cliente_id: int, dados: RepresentanteDados) -> Representante:
    """O cliente passa a ser representante, com o próximo código."""
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise DadoInvalido("Cliente não encontrado")
    outro = db.scalar(select(Representante).where(Representante.cliente_id == cliente_id))
    if outro is not None:
        raise Duplicado(f"{cliente.nome} já é o representante {outro.codigo}")
    codigo = (db.scalar(select(func.max(Representante.codigo))) or 0) + 1
    representante = Representante(codigo=codigo, cliente=cliente)
    _aplicar(representante, dados)
    db.add(representante)
    db.commit()
    return representante


def alterar(db: Session, representante_id: int, dados: RepresentanteDados) -> Representante:
    representante = obter(db, representante_id)
    _aplicar(representante, dados)
    db.commit()
    return representante


def alterar_limites(db: Session, representante_id: int, dados: LimitesDados) -> Representante:
    """Limite, bloqueio e comissões (permissão própria, como no VB6). Comissão vazia volta para a padrão."""
    representante = obter(db, representante_id)
    motivo = (dados.motivo_bloqueio or "").strip() or None
    if dados.bloqueado and not motivo:
        raise DadoInvalido("Informe o motivo do bloqueio")
    desconhecidos = [c.tipo_cobranca for c in dados.comissoes if c.tipo_cobranca not in COMISSOES_PADRAO]
    if desconhecidos:
        raise DadoInvalido(f"Tipo de cobrança desconhecido: {', '.join(desconhecidos)}")
    representante.limite, representante.bloqueado = dados.limite, dados.bloqueado
    representante.motivo_bloqueio = motivo if dados.bloqueado else None
    representante.bloqueia_impressao, representante.bloqueia_devolucao = dados.bloqueia_impressao, dados.bloqueia_devolucao
    representante.comissoes = [ComissaoRepresentante(tipo_cobranca=c.tipo_cobranca, percentual=c.percentual.quantize(Decimal("0.01")))
                               for c in dados.comissoes if c.percentual is not None]
    db.commit()
    return representante


def trocar_senha(db: Session, representante_id: int, senha: str) -> Representante:
    representante = obter(db, representante_id)
    representante.senha_hash = gerar_hash(senha, sem_caixa=True)
    db.commit()
    return representante


def conferir_senha(representante: Representante, senha: str) -> bool:
    """A senha que o representante digita no balcão para confirmar a transferência. Como no VB6, sem diferenciar
    maiúsculas."""
    return conferir_hash(senha, representante.senha_hash, sem_caixa=True)


# --- transferência: o representante leva produtos para o estoque dele ---

def documento(transferencia: Transferencia) -> str:
    return f"transferência {transferencia.numero}"


def em_uso(db: Session, empresa_id: int, representante_id: int) -> list[tuple]:
    """O que está com o representante na loja: (produto, restante, preço da transferência), item a item."""
    return list(db.execute(
        select(Produto, ItemTransferencia.restante, ItemTransferencia.preco)
        .join(ItemTransferencia.transferencia).join(Produto, ItemTransferencia.produto_id == Produto.id)
        .where(Transferencia.empresa_id == empresa_id, Transferencia.representante_id == representante_id,
               Transferencia.situacao == CONFIRMADA, ItemTransferencia.restante > 0)).all())


def _centavos(valor: Decimal) -> Decimal:
    return valor.quantize(ZERO, rounding=ROUND_HALF_UP)


def posicao(db: Session, empresa_id: int, representante: Representante) -> dict:
    """O estoque consignado do representante, por produto, pelo preço da transferência (é o que conta no limite) e
    pelo preço atual."""
    produtos: dict[int, dict] = {}
    for produto, restante, preco in em_uso(db, empresa_id, representante.id):
        linha = produtos.setdefault(produto.id, {
            "produto_id": produto.id, "codigo": produto.codigo, "descricao": produto.nome, "quantidade": ZERO3,
            "total_transferencia": ZERO, "total_atual": ZERO})
        linha["quantidade"] += restante
        linha["total_transferencia"] += _centavos(restante * preco)
        linha["total_atual"] += _centavos(restante * produto.preco_venda)
    itens = sorted(produtos.values(), key=lambda linha: linha["descricao"])
    usado = sum((linha["total_transferencia"] for linha in itens), ZERO)
    return {"limite": representante.limite, "em_uso": usado,
            "em_uso_atual": sum((linha["total_atual"] for linha in itens), ZERO),
            "disponivel": representante.limite - usado, "pecas": sum((linha["quantidade"] for linha in itens), ZERO3),
            "itens": itens}


def _pode_levar(representante: Representante) -> None:
    if not representante.ativo:
        raise DadoInvalido(f"O representante {representante.codigo} está inativo")
    if representante.bloqueado:
        raise DadoInvalido(f"O representante {representante.codigo} está bloqueado e não leva mercadoria: "
                           f"{representante.motivo_bloqueio}")


def transferencias(db: Session, empresa_id: int, representante_id: int | None = None, situacao: str | None = None,
                   limite: int = 100) -> list[Transferencia]:
    consulta = select(Transferencia).where(Transferencia.empresa_id == empresa_id)
    if representante_id:
        consulta = consulta.where(Transferencia.representante_id == representante_id)
    if situacao:
        consulta = consulta.where(Transferencia.situacao == situacao)
    return list(db.scalars(consulta.order_by(Transferencia.id.desc()).limit(limite)))


def obter_transferencia(db: Session, empresa_id: int, transferencia_id: int) -> Transferencia:
    transferencia = db.get(Transferencia, transferencia_id)
    if transferencia is None or transferencia.empresa_id != empresa_id:
        raise NaoEncontrado("Transferência não encontrada")
    return transferencia


def _aberta(db: Session, empresa_id: int, transferencia_id: int) -> Transferencia:
    transferencia = obter_transferencia(db, empresa_id, transferencia_id)
    if transferencia.situacao != ABERTA:
        raise DadoInvalido("A transferência já foi confirmada")
    return transferencia


def abrir_transferencia(db: Session, empresa_id: int, usuario: Usuario, representante_id: int) -> Transferencia:
    """Começa a transferência do representante; se ele já tem uma aberta na loja, é ela que continua."""
    representante = obter(db, representante_id)
    _pode_levar(representante)
    aberta = db.scalar(select(Transferencia).where(
        Transferencia.empresa_id == empresa_id, Transferencia.representante_id == representante_id,
        Transferencia.situacao == ABERTA))
    if aberta is not None:
        return aberta
    numero = (db.scalar(select(func.max(Transferencia.numero)).where(Transferencia.empresa_id == empresa_id)) or 0) + 1
    transferencia = Transferencia(empresa_id=empresa_id, numero=numero, representante=representante, situacao=ABERTA,
                                  total=ZERO, atendida_por=usuario)
    db.add(transferencia)
    db.commit()
    return transferencia


def _recalcular(transferencia: Transferencia) -> None:
    transferencia.total = sum((i.total for i in transferencia.itens), ZERO)


def _inteira(quantidade: Decimal) -> bool:
    return quantidade == quantidade.to_integral_value()


def incluir_item(db: Session, empresa_id: int, transferencia_id: int, produto_id: int,
                 quantidade: Decimal) -> Transferencia:
    """Sai pelo preço de venda do dia. O mesmo produto de novo soma na linha que já existe."""
    transferencia = _aberta(db, empresa_id, transferencia_id)
    produto = db.get(Produto, produto_id)
    if produto is None:
        raise NaoEncontrado("Produto não encontrado")
    item = next((i for i in transferencia.itens if i.produto_id == produto.id), None)
    total = quantidade + (item.quantidade if item else ZERO3)
    if not produto.fracionado and not _inteira(total):
        raise DadoInvalido(f"{produto.nome} não aceita quantidade com fração")
    if item is None:
        transferencia.itens.append(ItemTransferencia(
            ordem=max((i.ordem for i in transferencia.itens), default=0) + 1, produto=produto, descricao=produto.nome,
            quantidade=total, preco=produto.preco_venda, restante=ZERO3))
    else:
        item.quantidade = total
    _recalcular(transferencia)
    db.commit()
    return transferencia


def alterar_item(db: Session, empresa_id: int, transferencia_id: int, item_id: int,
                 quantidade: Decimal) -> Transferencia:
    """Quantidade zero tira o item."""
    transferencia = _aberta(db, empresa_id, transferencia_id)
    item = next((i for i in transferencia.itens if i.id == item_id), None)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    if quantidade <= 0:
        transferencia.itens.remove(item)
    else:
        if not item.produto.fracionado and not _inteira(quantidade):
            raise DadoInvalido(f"{item.descricao} não aceita quantidade com fração")
        item.quantidade = quantidade
    _recalcular(transferencia)
    db.commit()
    return transferencia


def descartar_transferencia(db: Session, empresa_id: int, transferencia_id: int) -> None:
    """A aberta não mexeu em nada: some."""
    db.delete(_aberta(db, empresa_id, transferencia_id))
    db.commit()


def confirmar(db: Session, empresa_id: int, usuario: Usuario, transferencia_id: int,
              senha: str) -> tuple[Transferencia, list[str]]:
    """O representante confirma com a senha dele: os produtos passam ao estoque dele (o reservado da loja). Bloqueado
    ou passando do limite (pelo preço da transferência), não leva. Devolve os avisos de estoque da loja."""
    transferencia = _aberta(db, empresa_id, transferencia_id)
    representante = transferencia.representante
    _pode_levar(representante)
    if not transferencia.itens:
        raise DadoInvalido("A transferência não tem produtos")
    if not representante.senha_hash:
        raise DadoInvalido("O representante não tem senha: cadastre-a na ficha dele")
    if not conferir_senha(representante, senha):
        raise DadoInvalido("A senha do representante não confere")
    usado = posicao(db, empresa_id, representante)["em_uso"]
    if usado + transferencia.total > representante.limite:
        raise DadoInvalido(f"Passa do limite do representante: ele já está com {moeda(usado)}, esta transferência é de "
                           f"{moeda(transferencia.total)} e o limite é {moeda(representante.limite)}")
    avisos = []
    for item in transferencia.itens:
        item.restante = item.quantidade
        try:
            movimento = estoque.movimentar(db, empresa_id, item.produto_id, "consignacao_envio",
                                           reservado=item.quantidade, usuario_id=usuario.id,
                                           documento=documento(transferencia))
        except estoque.ErroEstoque as e:
            raise DadoInvalido(str(e))
        disponivel = movimento.saldo - movimento.saldo_reservado
        if disponivel < 0:
            avisos.append(f"{item.descricao}: o disponível na loja ficou em {disponivel.normalize():f}")
    transferencia.situacao, transferencia.confirmada_em = CONFIRMADA, datetime.now()
    db.commit()
    return transferencia, avisos


# --- devolução: o representante devolve produtos à loja, sem custo ---

PERMISSAO_LIBERAR = "consignacao.liberar"  # o gerente, para o representante com a devolução bloqueada


class PedeAutorizacao(ErroConsignacao):
    """O representante tem a devolução bloqueada: a tela pede o login e a senha do gerente e manda de novo."""


def com_ele(db: Session, empresa_id: int, representante_id: int) -> list[ItemTransferencia]:
    """Os itens de transferência que ainda têm resto com o representante, um por transferência (o mesmo produto
    aparece repetido se veio em transferências diferentes), dos mais antigos aos mais novos."""
    return list(db.scalars(
        select(ItemTransferencia).join(ItemTransferencia.transferencia)
        .where(Transferencia.empresa_id == empresa_id, Transferencia.representante_id == representante_id,
               Transferencia.situacao == CONFIRMADA, ItemTransferencia.restante > 0)
        .order_by(Transferencia.confirmada_em, ItemTransferencia.ordem)))


def devolucoes(db: Session, empresa_id: int, representante_id: int | None = None, limite: int = 100) -> list[Devolucao]:
    consulta = select(Devolucao).where(Devolucao.empresa_id == empresa_id)
    if representante_id:
        consulta = consulta.where(Devolucao.representante_id == representante_id)
    return list(db.scalars(consulta.order_by(Devolucao.id.desc()).limit(limite)))


def obter_devolucao(db: Session, empresa_id: int, devolucao_id: int) -> Devolucao:
    devolucao = db.get(Devolucao, devolucao_id)
    if devolucao is None or devolucao.empresa_id != empresa_id:
        raise NaoEncontrado("Devolução não encontrada")
    return devolucao


def _devolucao_aberta(db: Session, empresa_id: int, devolucao_id: int) -> Devolucao:
    devolucao = obter_devolucao(db, empresa_id, devolucao_id)
    if devolucao.situacao != ABERTA:
        raise DadoInvalido("A devolução já foi confirmada")
    return devolucao


def abrir_devolucao(db: Session, empresa_id: int, usuario: Usuario, representante_id: int) -> Devolucao:
    """Começa a devolução do representante (o bloqueado também devolve); se já tem uma aberta, é ela."""
    representante = obter(db, representante_id)
    aberta = db.scalar(select(Devolucao).where(
        Devolucao.empresa_id == empresa_id, Devolucao.representante_id == representante_id, Devolucao.situacao == ABERTA))
    if aberta is not None:
        return aberta
    numero = (db.scalar(select(func.max(Devolucao.numero)).where(Devolucao.empresa_id == empresa_id)) or 0) + 1
    devolucao = Devolucao(empresa_id=empresa_id, numero=numero, representante=representante, situacao=ABERTA,
                          retificadora=False, total=ZERO, atendida_por=usuario)
    db.add(devolucao)
    db.commit()
    return devolucao


def _recalcular_devolucao(devolucao: Devolucao) -> None:
    devolucao.total = sum((i.total for i in devolucao.itens), ZERO)


def incluir_na_devolucao(db: Session, empresa_id: int, devolucao_id: int, item_transferencia_id: int,
                         quantidade: Decimal) -> Devolucao:
    """A peça volta do item de transferência escolhido; não mais do que resta dele com o representante."""
    devolucao = _devolucao_aberta(db, empresa_id, devolucao_id)
    origem = db.get(ItemTransferencia, item_transferencia_id)
    transferencia = origem.transferencia if origem else None
    if (transferencia is None or transferencia.empresa_id != empresa_id or transferencia.situacao != CONFIRMADA
            or transferencia.representante_id != devolucao.representante_id):
        raise NaoEncontrado("Este produto não está com o representante")
    item = next((i for i in devolucao.itens if i.item_transferencia_id == origem.id), None)
    total = quantidade + (item.quantidade if item else ZERO3)
    if not origem.produto.fracionado and not _inteira(total):
        raise DadoInvalido(f"{origem.descricao} não aceita quantidade com fração")
    if total > origem.restante:
        raise DadoInvalido(f"{origem.descricao}: só restam {origem.restante.normalize():f} desta transferência "
                           f"({transferencia.numero}) com o representante")
    if item is None:
        devolucao.itens.append(ItemDevolucao(ordem=max((i.ordem for i in devolucao.itens), default=0) + 1,
                                             item_transferencia=origem, quantidade=total))
    else:
        item.quantidade = total
    _recalcular_devolucao(devolucao)
    db.commit()
    return devolucao


def alterar_na_devolucao(db: Session, empresa_id: int, devolucao_id: int, item_id: int, quantidade: Decimal) -> Devolucao:
    """Quantidade zero tira o item."""
    devolucao = _devolucao_aberta(db, empresa_id, devolucao_id)
    item = next((i for i in devolucao.itens if i.id == item_id), None)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    origem = item.item_transferencia
    if quantidade <= 0:
        devolucao.itens.remove(item)
    else:
        if not origem.produto.fracionado and not _inteira(quantidade):
            raise DadoInvalido(f"{origem.descricao} não aceita quantidade com fração")
        if quantidade > origem.restante:
            raise DadoInvalido(f"{origem.descricao}: só restam {origem.restante.normalize():f} com o representante")
        item.quantidade = quantidade
    _recalcular_devolucao(devolucao)
    db.commit()
    return devolucao


def alterar_devolucao(db: Session, empresa_id: int, devolucao_id: int, retificadora: bool,
                      observacao: str | None) -> Devolucao:
    devolucao = _devolucao_aberta(db, empresa_id, devolucao_id)
    devolucao.retificadora, devolucao.observacao = retificadora, (observacao or "").strip() or None
    db.commit()
    return devolucao


def descartar_devolucao(db: Session, empresa_id: int, devolucao_id: int) -> None:
    db.delete(_devolucao_aberta(db, empresa_id, devolucao_id))
    db.commit()


def _liberacao(db: Session, empresa_id: int, permissoes: set[str], login: str | None, senha: str | None,
               permissao: str = PERMISSAO_LIBERAR,
               motivo: str = "A devolução deste representante está bloqueada: só com a liberação do gerente",
               o_que: str = "liberar a devolução bloqueada") -> Usuario | None:
    """Quem libera: quem tem a permissão (None: o próprio usuário), ou o gerente que digita o login e a senha."""
    if permissao in permissoes:
        return None
    if not login or not senha:
        raise PedeAutorizacao(motivo)
    try:
        gerente = acesso.autenticar(db, login, senha)
    except acesso.ErroAcesso:
        raise PedeAutorizacao("Login ou senha de quem libera não confere")
    if permissao not in acesso.permissoes_na_empresa(db, gerente, empresa_id):
        raise PedeAutorizacao(f"{gerente.nome} não pode {o_que}")
    return gerente


def confirmar_devolucao(db: Session, empresa_id: int, usuario: Usuario, permissoes: set[str], devolucao_id: int,
                        senha: str, login_gerente: str | None = None, senha_gerente: str | None = None) -> Devolucao:
    """O representante confirma com a senha dele: as peças saem do que está com ele e voltam para a loja (o
    reservado do estoque baixa). Com a devolução bloqueada, pede a liberação do gerente."""
    devolucao = _devolucao_aberta(db, empresa_id, devolucao_id)
    representante = devolucao.representante
    if not devolucao.itens:
        raise DadoInvalido("A devolução não tem produtos")
    if not representante.senha_hash:
        raise DadoInvalido("O representante não tem senha: cadastre-a na ficha dele")
    if not conferir_senha(representante, senha):
        raise DadoInvalido("A senha do representante não confere")
    if representante.bloqueia_devolucao:
        devolucao.autorizada_por = _liberacao(db, empresa_id, permissoes, login_gerente, senha_gerente)
    for item in devolucao.itens:
        origem = item.item_transferencia
        if item.quantidade > origem.restante:  # outra devolução ou um acerto baixou antes
            raise DadoInvalido(f"{origem.descricao}: só restam {origem.restante.normalize():f} com o representante")
        origem.restante -= item.quantidade
        try:
            estoque.movimentar(db, empresa_id, origem.produto_id, "consignacao_devolucao", reservado=-item.quantidade,
                               usuario_id=usuario.id, documento=f"devolução {devolucao.numero}",
                               observacao="retificadora" if devolucao.retificadora else None)
        except estoque.ErroEstoque as e:
            raise DadoInvalido(str(e))
    devolucao.situacao, devolucao.confirmada_em = CONFIRMADA, datetime.now()
    db.commit()
    return devolucao


# --- acerto: o que o representante vendeu vira dinheiro ou carnê ---

PERMISSAO_LIMITE = "vendas.autorizar"  # a gerência, como no crediário da venda acima do limite do cliente
# no acerto à vista, as formas que valem para cada comissão
FORMAS_DA_COMISSAO = {
    "vista_dinheiro": ("dinheiro", "pix", "deposito"),
    "vista_cartao": ("cartao_debito", "cartao_credito"),
    "vista_parcelado": ("cartao_credito",),
}


def acertos(db: Session, empresa_id: int, representante_id: int | None = None, limite: int = 100) -> list[Acerto]:
    consulta = select(Acerto).where(Acerto.empresa_id == empresa_id)
    if representante_id:
        consulta = consulta.where(Acerto.representante_id == representante_id)
    return list(db.scalars(consulta.order_by(Acerto.id.desc()).limit(limite)))


def obter_acerto(db: Session, empresa_id: int, acerto_id: int) -> Acerto:
    acerto = db.get(Acerto, acerto_id)
    if acerto is None or acerto.empresa_id != empresa_id:
        raise NaoEncontrado("Acerto não encontrado")
    return acerto


def _acerto_aberto(db: Session, empresa_id: int, acerto_id: int) -> Acerto:
    acerto = obter_acerto(db, empresa_id, acerto_id)
    if acerto.situacao != ABERTA:
        raise DadoInvalido("O acerto já foi confirmado")
    return acerto


def carne_do_acerto(db: Session, acerto: Acerto) -> ContaReceber | None:
    return db.scalar(select(ContaReceber).where(ContaReceber.acerto_id == acerto.id))


def _tipo_padrao(acerto: Acerto) -> str:
    if acerto.queima:
        return "queima"
    if acerto.pagamento == A_VISTA:
        return "vista_dinheiro"
    return "cliente" if acerto.para == PARA_CLIENTE else "representante"


def _recalcular_acerto(acerto: Acerto) -> None:
    """comissão = % × o total inicial + a diferença; para o representante, ela sai do valor (é o desconto dele)."""
    acerto.percentual = acerto.representante.comissao(acerto.tipo_comissao)
    acerto.total_inicial = sum((i.total for i in acerto.itens), ZERO)
    acerto.comissao = _centavos(acerto.percentual * acerto.total_inicial / 100) + acerto.diferenca
    acerto.valor = acerto.negociado - (acerto.comissao if acerto.para == PARA_REPRESENTANTE else ZERO)


def abrir_acerto(db: Session, empresa_id: int, usuario: Usuario, representante_id: int) -> Acerto:
    """Começa o acerto do representante (o bloqueado também acerta); se já tem um aberto, é ele."""
    representante = obter(db, representante_id)
    aberto = db.scalar(select(Acerto).where(
        Acerto.empresa_id == empresa_id, Acerto.representante_id == representante_id, Acerto.situacao == ABERTA))
    if aberto is not None:
        return aberto
    numero = (db.scalar(select(func.max(Acerto.numero)).where(Acerto.empresa_id == empresa_id)) or 0) + 1
    acerto = Acerto(empresa_id=empresa_id, numero=numero, representante=representante, situacao=ABERTA,
                    para=PARA_CLIENTE, queima=False, pagamento=A_PRAZO, tipo_comissao="cliente", diferenca=ZERO,
                    parcelas=1, atendida_por=usuario)
    _recalcular_acerto(acerto)
    db.add(acerto)
    db.commit()
    return acerto


def _preco_no_acerto(acerto: Acerto, origem: ItemTransferencia) -> Decimal:
    """No acerto de queima, só produto em queima, pelo preço de queima de hoje; nos outros, o da transferência."""
    if not acerto.queima:
        return origem.preco
    if origem.produto.preco_queima is None:
        raise DadoInvalido(f"{origem.descricao} não está em queima: o acerto de queima é só de produtos em queima")
    return origem.produto.preco_queima


def alterar_acerto(db: Session, empresa_id: int, acerto_id: int, dados: AcertoDados) -> Acerto:
    """Para quem, o cliente, queima, à vista ou a prazo, o tipo de cobrança, o valor negociado e as parcelas."""
    acerto = _acerto_aberto(db, empresa_id, acerto_id)
    representante = acerto.representante
    if dados.para == PARA_CLIENTE:
        if dados.pagamento == A_VISTA:
            raise DadoInvalido("O acerto à vista é só para o próprio representante")
        if dados.queima:
            raise DadoInvalido("O acerto de queima é só para o próprio representante, à vista")
        cliente = db.get(Cliente, dados.cliente_id) if dados.cliente_id else None
        if dados.cliente_id and cliente is None:
            raise NaoEncontrado("Cliente não encontrado")
        if cliente is not None and cliente.id == representante.cliente_id:
            raise DadoInvalido("Para o próprio representante, escolha o acerto para ele")
    else:
        cliente = representante.cliente
        if dados.queima and dados.pagamento != A_VISTA:
            raise DadoInvalido("O acerto de queima é à vista")
    tipo = dados.tipo_comissao
    if dados.queima:
        tipo = "queima"
    elif dados.pagamento == A_VISTA:
        tipo = tipo if tipo in FORMAS_DA_COMISSAO else "vista_dinheiro"
    elif tipo not in TIPOS_COBRANCA:
        tipo = "cliente" if dados.para == PARA_CLIENTE else "representante"
    if dados.primeiro_vencimento and dados.primeiro_vencimento < date.today():
        raise DadoInvalido("O primeiro vencimento não pode ser antes de hoje")
    acerto.para, acerto.cliente, acerto.pagamento, acerto.tipo_comissao = dados.para, cliente, dados.pagamento, tipo
    if acerto.queima != dados.queima:
        acerto.queima = dados.queima
        for item in acerto.itens:
            item.preco = _preco_no_acerto(acerto, item.item_transferencia)
    acerto.parcelas, acerto.primeiro_vencimento = dados.parcelas, dados.primeiro_vencimento
    _recalcular_acerto(acerto)
    # o valor negociado manda; sem ele, fica a diferença que já tinha
    if dados.negociado is not None:
        acerto.diferenca = dados.negociado - acerto.total_inicial
        _recalcular_acerto(acerto)
    db.commit()
    return acerto


def incluir_no_acerto(db: Session, empresa_id: int, acerto_id: int, item_transferencia_id: int,
                      quantidade: Decimal) -> Acerto:
    """A peça sai do item de transferência escolhido, como na devolução; não mais do que resta dele."""
    acerto = _acerto_aberto(db, empresa_id, acerto_id)
    origem = db.get(ItemTransferencia, item_transferencia_id)
    transferencia = origem.transferencia if origem else None
    if (transferencia is None or transferencia.empresa_id != empresa_id or transferencia.situacao != CONFIRMADA
            or transferencia.representante_id != acerto.representante_id):
        raise NaoEncontrado("Este produto não está com o representante")
    item = next((i for i in acerto.itens if i.item_transferencia_id == origem.id), None)
    total = quantidade + (item.quantidade if item else ZERO3)
    if not origem.produto.fracionado and not _inteira(total):
        raise DadoInvalido(f"{origem.descricao} não aceita quantidade com fração")
    if total > origem.restante:
        raise DadoInvalido(f"{origem.descricao}: só restam {origem.restante.normalize():f} desta transferência "
                           f"({transferencia.numero}) com o representante")
    if item is None:
        acerto.itens.append(ItemAcerto(ordem=max((i.ordem for i in acerto.itens), default=0) + 1,
                                       item_transferencia=origem, quantidade=total,
                                       preco=_preco_no_acerto(acerto, origem)))
    else:
        item.quantidade = total
    _recalcular_acerto(acerto)
    db.commit()
    return acerto


def alterar_no_acerto(db: Session, empresa_id: int, acerto_id: int, item_id: int, quantidade: Decimal) -> Acerto:
    """Quantidade zero tira o item."""
    acerto = _acerto_aberto(db, empresa_id, acerto_id)
    item = next((i for i in acerto.itens if i.id == item_id), None)
    if item is None:
        raise NaoEncontrado("Item não encontrado")
    origem = item.item_transferencia
    if quantidade <= 0:
        acerto.itens.remove(item)
    else:
        if not origem.produto.fracionado and not _inteira(quantidade):
            raise DadoInvalido(f"{origem.descricao} não aceita quantidade com fração")
        if quantidade > origem.restante:
            raise DadoInvalido(f"{origem.descricao}: só restam {origem.restante.normalize():f} com o representante")
        item.quantidade = quantidade
    _recalcular_acerto(acerto)
    db.commit()
    return acerto


def descartar_acerto(db: Session, empresa_id: int, acerto_id: int) -> None:
    db.delete(_acerto_aberto(db, empresa_id, acerto_id))
    db.commit()


def _forma_crediario(db: Session) -> FormaPagamento:
    forma = db.scalar(select(FormaPagamento).where(FormaPagamento.tipo == "crediario")
                      .order_by(FormaPagamento.ativo.desc(), FormaPagamento.id))
    if forma is None:
        raise DadoInvalido("Cadastre a forma de pagamento Crediário: é nela que o carnê do acerto entra no caixa")
    return forma


def _pagamentos_do_acerto(db: Session, acerto: Acerto, pagamentos: list[PagamentoDados]) -> list[PagamentoAcerto]:
    linhas = []
    for ordem, dados in enumerate(pagamentos, start=1):
        forma = db.get(FormaPagamento, dados.forma_pagamento_id)
        if forma is None:
            raise NaoEncontrado("Forma de pagamento não encontrada")
        if not forma.ativo:
            raise DadoInvalido(f"A forma {forma.nome} está desativada; escolha outra")
        if forma.tipo == "crediario":
            raise DadoInvalido("O crediário não entra como pagamento à vista: é o carnê do acerto a prazo")
        if dados.parcelas > forma.parcelas:
            raise DadoInvalido(f"{forma.nome} vai até {forma.parcelas}x")
        if acerto.pagamento == A_VISTA and not acerto.queima:
            # a comissão foi pelo jeito de pagar: o pagamento tem que ser desse jeito
            nome = COMISSOES_ACERTO[acerto.tipo_comissao][0]
            if forma.tipo not in FORMAS_DA_COMISSAO[acerto.tipo_comissao]:
                raise DadoInvalido(f"{nome}: não pode ser pago em {forma.nome}")
            if (acerto.tipo_comissao == "vista_parcelado") != (dados.parcelas > 1):
                raise DadoInvalido(f"{nome}: {forma.nome} em {dados.parcelas}x não vale")
        linhas.append(PagamentoAcerto(ordem=ordem, forma_pagamento=forma, valor=dados.valor, parcelas=dados.parcelas))
    return linhas


def _conferir_credito(db: Session, acerto: Acerto, a_prazo: Decimal, usuario: Usuario, permissoes: set[str],
                      login: str | None, senha: str | None) -> None:
    """O carnê vai até o limite disponível de quem paga (o cliente, ou o próprio representante), como na venda;
    acima, só com a gerência."""
    credito = contas.credito(db, acerto.cliente)
    if credito.impedimento:
        raise DadoInvalido(credito.impedimento.replace("comprar no crediário", "receber o acerto a prazo"))
    if a_prazo <= credito.disponivel:
        return
    mensagem = (f"O carnê de {moeda(a_prazo)} passa do limite disponível de {acerto.cliente.nome} "
                f"({moeda(max(credito.disponivel, ZERO))}). Peça a autorização da gerência.")
    gerente = _liberacao(db, acerto.empresa_id, permissoes, login, senha, PERMISSAO_LIMITE, mensagem,
                         "autorizar o carnê acima do limite")
    acerto.autorizada_por = gerente or usuario


def confirmar_acerto(db: Session, empresa_id: int, usuario: Usuario, permissoes: set[str], acerto_id: int,
                     sessao_caixa_id: int, pagamentos: list[PagamentoDados], login_gerente: str | None = None,
                     senha_gerente: str | None = None) -> Acerto:
    """Fecha o acerto no caixa do consignado (sem a senha do representante): as peças saem do que está com ele e da
    loja, o que foi pago entra no caixa e o resto vira o carnê, com a comissão do acerto para o cliente dividida
    pelas parcelas."""
    acerto = _acerto_aberto(db, empresa_id, acerto_id)
    representante = acerto.representante
    if not acerto.itens:
        raise DadoInvalido("O acerto não tem produtos")
    if acerto.cliente is None:
        raise DadoInvalido("Escolha o cliente do acerto")
    if acerto.valor <= 0:
        raise DadoInvalido("O valor do acerto tem que ser maior que zero")
    try:
        sessao = caixa.obter_sessao(db, empresa_id, sessao_caixa_id)
    except caixa.ErroCaixa as e:
        raise NaoEncontrado(str(e))
    if sessao.situacao != ABERTO:
        raise DadoInvalido(f"O caixa {sessao.caixa.nome} está fechado")
    acerto.pagamentos = _pagamentos_do_acerto(db, acerto, pagamentos)
    pago = acerto.entrada
    if acerto.pagamento == A_VISTA:
        if pago != acerto.valor:
            raise DadoInvalido(f"O pago ({moeda(pago)}) tem que ser o valor do acerto, {moeda(acerto.valor)}")
    else:
        if acerto.para == PARA_REPRESENTANTE and representante.bloqueado:
            raise DadoInvalido(f"O representante {representante.codigo} está bloqueado: para ele, só acerto à vista "
                               f"({representante.motivo_bloqueio})")
        if pago >= acerto.valor:
            raise DadoInvalido("A entrada cobre o acerto todo: faça à vista")
        if not acerto.primeiro_vencimento:
            raise DadoInvalido("Informe o primeiro vencimento")
        crediario = _forma_crediario(db)
        if acerto.parcelas > crediario.parcelas:
            raise DadoInvalido(f"O carnê vai até {crediario.parcelas}x")
        _conferir_credito(db, acerto, acerto.a_prazo, usuario, permissoes, login_gerente, senha_gerente)

    for item in acerto.itens:
        origem = item.item_transferencia
        if item.quantidade > origem.restante:  # uma devolução ou outro acerto baixou antes
            raise DadoInvalido(f"{origem.descricao}: só restam {origem.restante.normalize():f} com o representante")
        origem.restante -= item.quantidade
        try:
            estoque.movimentar(db, empresa_id, origem.produto_id, "consignacao_acerto", -item.quantidade,
                               reservado=-item.quantidade, usuario_id=usuario.id, documento=f"acerto {acerto.numero}")
        except estoque.ErroEstoque as e:
            raise DadoInvalido(str(e))

    documento_caixa = f"acerto {acerto.numero}"
    lancamentos = [(p.forma_pagamento, p.valor) for p in acerto.pagamentos]
    if acerto.pagamento == A_PRAZO:
        lancamentos.append((crediario, acerto.a_prazo))
        conta = contas.lancar_carne(db, empresa_id, acerto.cliente.id, None, acerto.a_prazo, acerto.parcelas,
                                    acerto.primeiro_vencimento, crediario.intervalo,
                                    f"Acerto {acerto.numero} {acerto.cliente.nome}", usuario.id, acerto.tipo_comissao)
        conta.origem, conta.acerto_id = "acerto", acerto.id
        if acerto.para == PARA_CLIENTE and acerto.comissao > 0:
            db.flush()
            for parcela, parte in zip(conta.parcelas, contas.dividir(acerto.comissao, len(conta.parcelas))):
                db.add(ComissaoParcela(acerto_id=acerto.id, representante_id=representante.id, parcela_id=parcela.id,
                                       valor=parte))
    for forma, valor in lancamentos:
        db.add(LancamentoCaixa(sessao_id=sessao.id, tipo="entrada", motivo="acerto", forma_pagamento_id=forma.id,
                               valor=valor, documento=documento_caixa, usuario_id=usuario.id))
    acerto.sessao_caixa_id = sessao.id
    acerto.situacao, acerto.confirmada_em = CONFIRMADA, datetime.now()
    db.commit()
    return acerto

