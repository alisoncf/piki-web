import pytest
from app.dominios.acesso import servico
from app.dominios.acesso.cores import PALETA, cor_padrao
from app.dominios.acesso.modelos import Empresa


def test_cor_automatica_pelo_codigo():
    assert cor_padrao("01") == "azul"
    assert cor_padrao("02") == "laranja"
    assert cor_padrao("09") == "azul"  # depois da 8ª volta ao início
    assert cor_padrao("AB") in PALETA  # código não numérico também recebe uma cor


def test_login_traz_a_cor_de_cada_empresa(cliente, banco, cenario):
    with banco() as db:
        servico.definir_cor_empresa(db, db.get(Empresa, cenario["e2"]), "oliva")
    corpo = cliente.post("/auth/login", json={"login": "bia", "senha": "senha-bia"}).json()
    cores = {e["codigo"]: e["cor"] for e in corpo["empresas"]}
    assert cores == {"01": PALETA["azul"], "02": PALETA["oliva"]}


def test_cor_fora_da_paleta_e_recusada(banco, cenario):
    with banco() as db, pytest.raises(ValueError, match="Cor inexistente"):
        servico.definir_cor_empresa(db, db.get(Empresa, cenario["e1"]), "#ff0000")


def test_voltar_para_a_cor_automatica(banco, cenario):
    with banco() as db:
        emp = db.get(Empresa, cenario["e1"])
        servico.definir_cor_empresa(db, emp, "roxo")
        assert emp.cor_hex == PALETA["roxo"]
        servico.definir_cor_empresa(db, emp, None)
        assert emp.cor_hex == PALETA["azul"]
