"""Consultas do estoque."""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominios.estoque.modelos import Estoque, MovimentoEstoque


def estoque(db: Session, empresa_id: int, produto_id: int, travar: bool = False) -> Estoque | None:
    consulta = select(Estoque).where(Estoque.empresa_id == empresa_id, Estoque.produto_id == produto_id)
    if travar:  # dois movimentos ao mesmo tempo não se perdem (no PostgreSQL)
        consulta = consulta.with_for_update()
    return db.scalar(consulta)


def quantidades(db: Session, empresa_id: int, produto_ids: list[int]) -> dict[int, Decimal]:
    """O saldo de cada produto na loja (os que não têm linha ficam de fora: zero)."""
    if not produto_ids:
        return {}
    linhas = db.execute(select(Estoque.produto_id, Estoque.quantidade).where(
        Estoque.empresa_id == empresa_id, Estoque.produto_id.in_(produto_ids)))
    return dict(linhas.all())


def movimentos(db: Session, empresa_id: int, produto_id: int, limite: int,
               deslocamento: int) -> tuple[list[MovimentoEstoque], int]:
    """Do mais novo para o mais antigo."""
    filtro = (MovimentoEstoque.empresa_id == empresa_id, MovimentoEstoque.produto_id == produto_id)
    total = db.scalar(select(func.count()).select_from(MovimentoEstoque).where(*filtro))
    itens = db.scalars(select(MovimentoEstoque).where(*filtro).order_by(MovimentoEstoque.id.desc())
                       .limit(limite).offset(deslocamento))
    return list(itens), total
