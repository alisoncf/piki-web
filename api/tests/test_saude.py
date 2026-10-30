from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import sessao
from app.main import app


def test_saude_ok(cliente):
    r = cliente.get("/saude")
    assert r.status_code == 200
    assert r.json()["banco"] == "ok"


def test_filial_padrao(cliente):
    assert cliente.get("/saude").json()["cod_emp"] == "01"


def test_filial_pelo_cabecalho(cliente):
    r = cliente.get("/saude", headers={"X-Cod-Emp": "03"})
    assert r.json()["cod_emp"] == "03"


def test_filial_invalida(cliente):
    assert cliente.get("/saude", headers={"X-Cod-Emp": "abc"}).status_code == 400


def test_banco_fora_do_ar(cliente):
    # banco inexistente: a API responde 503 em vez de quebrar
    eng = create_engine("mysql+pymysql://x:x@127.0.0.1:1/x", connect_args={"connect_timeout": 1})
    fabrica = sessionmaker(bind=eng)

    def sessao_quebrada():
        with fabrica() as s:
            yield s

    app.dependency_overrides[sessao] = sessao_quebrada
    r = cliente.get("/saude")
    assert r.status_code == 503
    assert r.json()["banco"] == "indisponível"
