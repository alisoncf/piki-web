"""Conexão com o banco e base dos modelos."""
from collections.abc import Iterator
from datetime import datetime
from functools import lru_cache

from sqlalchemy import DateTime, Engine, MetaData, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import configuracao

# nomes previsíveis para chaves e índices: deixa as migrações do Alembic estáveis
CONVENCAO_NOMES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO_NOMES)


class ComDatas:
    """Colunas de auditoria comuns."""

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


@lru_cache
def engine() -> Engine:
    # pool_pre_ping evita erro com conexões derrubadas pelo servidor
    return create_engine(configuracao().database_url, pool_pre_ping=True)


def sessao() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição."""
    fabrica = sessionmaker(bind=engine(), autoflush=False, expire_on_commit=False)
    with fabrica() as s:
        yield s
