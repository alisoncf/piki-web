"""Consultas de produtos, seções e marcas."""
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.dominios.produtos.modelos import CodigoBarras, Marca, Produto, ProdutoFornecedor, Secao, Subsecao
from app.nucleo.documentos import so_digitos


def listar_produtos(db: Session, busca: str | None = None, secao_id: int | None = None,
                    subsecao_id: int | None = None, marca_id: int | None = None, fornecedor_id: int | None = None,
                    ativo: bool | None = None, limite: int = 50, deslocamento: int = 0) -> tuple[list[Produto], int]:
    """Uma página de produtos em ordem de nome, e o total que atende aos filtros.

    A busca acha o produto pelo código, por um código de barras, pelo código do
    fornecedor ou por todas as palavras do nome, em qualquer ordem ("cama casal
    trento" acha "JOGO DE CAMA CASAL 04 PÇS TRENTO").
    """
    consulta = select(Produto)
    if busca and busca.strip():
        termo = busca.strip()
        palavras = [func.lower(Produto.nome).like(f"%{p}%") for p in termo.lower().split()]
        condicoes = [and_(*palavras)]
        condicoes.append(Produto.id.in_(
            select(ProdutoFornecedor.produto_id).where(func.lower(ProdutoFornecedor.codigo) == termo.lower())))
        if (digitos := so_digitos(termo)) and digitos == termo:
            if len(digitos) <= 9:
                condicoes.append(Produto.codigo == int(digitos))
            condicoes.append(Produto.id.in_(select(CodigoBarras.produto_id).where(CodigoBarras.codigo == digitos)))
        consulta = consulta.where(or_(*condicoes))
    if subsecao_id is not None:
        consulta = consulta.where(Produto.subsecao_id == subsecao_id)
    elif secao_id is not None:
        consulta = consulta.where(Produto.subsecao_id.in_(select(Subsecao.id).where(Subsecao.secao_id == secao_id)))
    if marca_id is not None:
        consulta = consulta.where(Produto.marca_id == marca_id)
    if fornecedor_id is not None:
        consulta = consulta.where(Produto.id.in_(
            select(ProdutoFornecedor.produto_id).where(ProdutoFornecedor.fornecedor_id == fornecedor_id)))
    if ativo is not None:
        consulta = consulta.where(Produto.ativo.is_(ativo))
    total = db.scalar(select(func.count()).select_from(consulta.subquery()))
    itens = db.scalars(consulta.order_by(Produto.nome, Produto.codigo).limit(limite).offset(deslocamento))
    return list(itens), total


def produto_por_codigo(db: Session, codigo: int) -> Produto | None:
    return db.scalar(select(Produto).where(Produto.codigo == codigo))


def dono_do_codigo_de_barras(db: Session, codigo: str) -> Produto | None:
    return db.scalar(select(Produto).join(CodigoBarras).where(CodigoBarras.codigo == codigo))


def proximo_codigo(db: Session) -> int:
    return (db.scalar(select(func.max(Produto.codigo))) or 0) + 1


def listar_secoes(db: Session) -> list[Secao]:
    return list(db.scalars(select(Secao).order_by(Secao.nome)))


def secao_por_nome(db: Session, nome: str) -> Secao | None:
    return db.scalar(select(Secao).where(func.lower(Secao.nome) == nome.lower()))


def subsecao_por_nome(db: Session, secao_id: int, nome: str) -> Subsecao | None:
    return db.scalar(select(Subsecao).where(Subsecao.secao_id == secao_id, func.lower(Subsecao.nome) == nome.lower()))


def listar_marcas(db: Session) -> list[Marca]:
    return list(db.scalars(select(Marca).order_by(Marca.nome)))


def marca_por_nome(db: Session, nome: str) -> Marca | None:
    return db.scalar(select(Marca).where(func.lower(Marca.nome) == nome.lower()))
