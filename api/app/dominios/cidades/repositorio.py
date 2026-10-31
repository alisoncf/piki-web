"""Consultas de cidades."""
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.dominios.cidades.modelos import Cidade, nome_de_busca


def buscar_cidades(db: Session, busca: str | None = None, uf: str | None = None, limite: int = 20) -> list[Cidade]:
    """Pelo nome, sem ligar para acentos; as que começam com o termo vêm antes."""
    consulta = select(Cidade)
    termo = nome_de_busca(busca)
    if termo:
        consulta = consulta.where(Cidade.nome_busca.like(f"%{termo}%")).order_by(
            case((Cidade.nome_busca.like(f"{termo}%"), 0), else_=1)
        )
    if uf:
        consulta = consulta.where(Cidade.uf == uf.upper())
    return list(db.scalars(consulta.order_by(Cidade.nome_busca, Cidade.uf).limit(limite)))


def cidade_por_codigo(db: Session, codigo_ibge: str) -> Cidade | None:
    return db.scalar(select(Cidade).where(Cidade.codigo_ibge == codigo_ibge))
