from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import configuracao


@lru_cache
def engine() -> Engine:
    # pool_pre_ping evita erro com conexões derrubadas pelo MariaDB (wait_timeout)
    return create_engine(configuracao().database_url, pool_pre_ping=True)


def sessao() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição."""
    fabrica = sessionmaker(bind=engine(), autoflush=False, expire_on_commit=False)
    with fabrica() as s:
        yield s
