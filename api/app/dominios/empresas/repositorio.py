"""Consultas de empresas."""
from sqlalchemy import select
from sqlalchemy.orm import Session, undefer

from app.dominios.empresas.modelos import Empresa, ImagemEmpresa


def listar_empresas(db: Session) -> list[Empresa]:
    """Todas, ativas ou não, em ordem de código."""
    return list(db.scalars(select(Empresa).order_by(Empresa.codigo)))


def empresa_por_codigo(db: Session, codigo: str) -> Empresa | None:
    return db.scalar(select(Empresa).where(Empresa.codigo == codigo))


def empresa_por_cnpj(db: Session, cnpj: str) -> Empresa | None:
    return db.scalar(select(Empresa).where(Empresa.cnpj == cnpj))


def imagem(db: Session, empresa_id: int, tipo: str) -> ImagemEmpresa | None:
    """Com o conteúdo, que não vem na lista de imagens da empresa."""
    return db.scalar(
        select(ImagemEmpresa)
        .where(ImagemEmpresa.empresa_id == empresa_id, ImagemEmpresa.tipo == tipo)
        .options(undefer(ImagemEmpresa.conteudo))
    )
