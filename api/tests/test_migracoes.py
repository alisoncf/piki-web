"""As migrações rodam do zero no SQLite (o banco padrão de quem desenvolve sem .env) e voltam."""
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.config import RAIZ


def test_migracoes_sobem_e_descem_no_sqlite(tmp_path):
    url = f"sqlite:///{(tmp_path / 'migracoes.db').as_posix()}"
    cfg = Config(str(RAIZ / "api" / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "api" / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)

    command.upgrade(cfg, "head")
    eng = create_engine(url)
    with eng.begin() as c:
        # as colunas de data precisam de um padrão que o SQLite entenda
        c.execute(text("INSERT INTO cargo (nome, vende, cobra, ativo) VALUES ('Teste', 0, 0, 1)"))
        assert c.execute(text("SELECT criado_em FROM cargo")).scalar() is not None
    eng.dispose()
    command.downgrade(cfg, "base")
