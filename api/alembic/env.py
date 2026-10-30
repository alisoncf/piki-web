from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.config import configuracao
from app.registro_modelos import Base

if context.config.config_file_name:
    fileConfig(context.config.config_file_name)

URL = context.config.get_main_option("sqlalchemy.url") or configuracao().database_url
alvo = Base.metadata


def _opcoes(url: str) -> dict:
    # SQLite não altera colunas no lugar; o modo batch recria a tabela
    return {"target_metadata": alvo, "render_as_batch": url.startswith("sqlite"), "compare_type": True}


if context.is_offline_mode():
    context.configure(url=URL, literal_binds=True, **_opcoes(URL))
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(URL).connect() as conexao:
        context.configure(connection=conexao, **_opcoes(URL))
        with context.begin_transaction():
            context.run_migrations()
