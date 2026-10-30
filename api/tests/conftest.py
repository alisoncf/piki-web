import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import sessao
from app.legado import senha as senha_legado
from app.main import app
from app.modelos import Funcionario, LegadoBase, Usuario, WebBase


@pytest.fixture
def banco():
    """SQLite em memória com as tabelas do legado usadas pela API e as tabelas novas.

    Nunca toca no banco real do .env.
    """
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    LegadoBase.metadata.create_all(eng)
    WebBase.metadata.create_all(eng)
    fabrica = sessionmaker(bind=eng, autoflush=False, expire_on_commit=False)

    def sessao_teste():
        with fabrica() as s:
            yield s

    app.dependency_overrides[sessao] = sessao_teste
    yield fabrica
    app.dependency_overrides.clear()


@pytest.fixture
def cliente(banco):
    return TestClient(app)


@pytest.fixture
def criar_usuario(banco):
    """Cria um usuário com a senha gravada no formato do VB6."""

    def _criar(cod_fun="001", apelido="MARIA", senha="SEGREDO", status="1", nome="Maria da Silva"):
        with banco() as s:
            s.add(Funcionario(cod_fun=cod_fun, nome=nome, apelido=apelido, cod_cargo="001", status="1"))
            s.add(Usuario(cod_fun=cod_fun, senha=senha_legado.codificar(senha), status=status, nivel="1"))
            s.commit()

    return _criar
