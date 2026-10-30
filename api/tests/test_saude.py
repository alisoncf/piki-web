from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.nucleo.banco import sessao


def test_saude_ok(cliente):
    r = cliente.get("/saude")
    assert r.status_code == 200
    assert r.json()["banco"] == "ok"


def test_banco_fora_do_ar(cliente):
    # banco inexistente: a API responde 503 em vez de quebrar
    eng = create_engine("sqlite:////caminho/que/nao/existe/x.db")
    fabrica = sessionmaker(bind=eng)

    def sessao_quebrada():
        with fabrica() as s:
            yield s

    app.dependency_overrides[sessao] = sessao_quebrada
    r = cliente.get("/saude")
    assert r.status_code == 503
    assert r.json()["banco"] == "indisponível"
