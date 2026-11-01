import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import configuracao
from app.dominios.acesso import servico
from app.dominios.empresas.esquemas import EmpresaNova
from app.dominios.empresas.servico import criar_empresa
from app.main import app
from app.nucleo import seguranca
from app.nucleo.banco import sessao
from app.registro_modelos import Base


@pytest.fixture(autouse=True)
def hash_rapido(monkeypatch):
    """Argon2 com custo mínimo nos testes. Em produção valem os parâmetros padrão."""
    monkeypatch.setattr(seguranca, "_hasher", PasswordHasher(time_cost=1, memory_cost=8, parallelism=1))


@pytest.fixture
def banco():
    """Banco de teste com todas as tabelas, recriado a cada teste. Nunca usa o banco do .env.

    Padrão: SQLite em memória. Para rodar contra um PostgreSQL de teste, defina
    PIKI_TESTE_DATABASE_URL no .env (ver .env.example).
    """
    url = configuracao().teste_database_url
    if url:
        eng = create_engine(url)
        Base.metadata.drop_all(eng)
    else:
        eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    fabrica = sessionmaker(bind=eng, autoflush=False, expire_on_commit=False)

    def sessao_teste():
        with fabrica() as s:
            yield s

    app.dependency_overrides[sessao] = sessao_teste
    yield fabrica
    app.dependency_overrides.clear()
    eng.dispose()


@pytest.fixture
def cliente(banco):
    return TestClient(app)


@pytest.fixture
def cenario(banco):
    """Três empresas, dois perfis e quatro usuários:

    - ana: só a empresa 01, como Gerente
    - bia: empresas 01 (Gerente) e 02 (Consulta)
    - caio: administrador, sem vínculos
    - davi: nenhum acesso
    A empresa 03 está desativada.
    """
    with banco() as db:
        e1 = criar_empresa(db, EmpresaNova(codigo="01", nome="Loja Centro"))
        e2 = criar_empresa(db, EmpresaNova(codigo="02", nome="Loja Bairro"))
        e3 = criar_empresa(db, EmpresaNova(codigo="03", nome="Loja Fechada", ativa=False))
        gerente = servico.criar_perfil(db, "Gerente", ["acesso.usuarios", "acesso.perfis"])
        consulta = servico.criar_perfil(db, "Consulta", [])
        ana = servico.criar_usuario(db, "ana", "Ana Lima", "senha-ana")
        bia = servico.criar_usuario(db, "bia", "Bia Souza", "senha-bia")
        servico.criar_usuario(db, "caio", "Caio Admin", "senha-caio", administrador=True)
        servico.criar_usuario(db, "davi", "Davi Sem Acesso", "senha-davi")
        servico.dar_acesso(db, ana, e1, gerente)
        servico.dar_acesso(db, bia, e1, gerente)
        servico.dar_acesso(db, bia, e2, consulta)
        servico.dar_acesso(db, bia, e3, gerente)  # empresa desativada: não deve aparecer
        return {"e1": e1.id, "e2": e2.id, "e3": e3.id}
