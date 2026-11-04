"""Regras da consignação (D30): o cadastro de representantes, a transferência e a devolução."""
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.dominios.clientes.modelos import Cliente
from app.dominios.consignacao.esquemas import LimitesDados, RepresentanteDados
from app.dominios.acesso import servico as acesso
from app.dominios.acesso.modelos import Usuario
from app.dominios.consignacao.modelos import (
    ABERTA, COMISSOES_PADRAO, CONFIRMADA, ComissaoRepresentante, Devolucao, ItemDevolucao, ItemTransferencia,
    Representante, Transferencia,
)
from app.dominios.estoque import servico as estoque
from app.dominios.produtos.modelos import Produto
from app.dominios.receber.modelos import TIPOS_COBRANCA
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
    """As comissões de todos os tipos de cobrança: a do representante, ou a padrão."""
    proprias = {c.tipo_cobranca for c in representante.comissoes}
    return [{"tipo_cobranca": tipo, "nome": nome, "percentual": representante.comissao(tipo), "padrao": tipo not in proprias}
            for tipo, (nome, _) in TIPOS_COBRANCA.items()]


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


def _liberacao(db: Session, empresa_id: int, permissoes: set[str], login: str | None, senha: str | None) -> Usuario | None:
    """Quem libera a devolução bloqueada: quem tem a permissão, ou o gerente que digita o login e a senha."""
    if PERMISSAO_LIBERAR in permissoes:
        return None
    if not login or not senha:
        raise PedeAutorizacao("A devolução deste representante está bloqueada: só com a liberação do gerente")
    try:
        gerente = acesso.autenticar(db, login, senha)
    except acesso.ErroAcesso:
        raise PedeAutorizacao("Login ou senha de quem libera não confere")
    if PERMISSAO_LIBERAR not in acesso.permissoes_na_empresa(db, gerente, empresa_id):
        raise PedeAutorizacao(f"{gerente.nome} não pode liberar a devolução bloqueada")
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
