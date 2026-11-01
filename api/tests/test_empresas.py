"""Cadastro de empresas: ficha, esquema de cores (D19) e imagens. Dados fictícios."""
import pytest

from app.dominios.cidades.modelos import Cidade
from app.dominios.empresas.tema import misturar, tema_automatico, tema_da_cor

CNPJ = "11222333000181"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 20
TEMA = {"principal": "#941d70", "fundo": "#fbf3f8", "menu": "#2a1f26"}


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    return _auth(cliente, "caio", cenario["e1"])


@pytest.fixture
def anapolis(banco):
    with banco() as db:
        cidade = Cidade(codigo_ibge="5201108", nome="Anápolis", uf="GO", nome_busca="anapolis")
        db.add(cidade)
        db.commit()
        return cidade.id


def test_tema_automatico_pelo_codigo():
    assert misturar("#000000", "#ffffff", 0.5) == "#808080"
    assert tema_da_cor("#2F6FB0") == {"principal": "#2f6fb0", "fundo": "#eef3f9", "menu": "#1f2835"}
    assert tema_automatico("01")["principal"] == "#2f6fb0"
    assert tema_automatico("02")["principal"] == "#d9822b"
    assert tema_automatico("09") == tema_automatico("01")  # depois da 8ª volta ao início


def test_lista_todas_com_o_tema(cliente, cenario, admin):
    r = cliente.get("/empresas", headers=admin)
    assert r.status_code == 200
    assert [(e["codigo"], e["ativa"]) for e in r.json()] == [("01", True), ("02", True), ("03", False)]
    assert r.json()[0]["tema"] == tema_automatico("01")
    ana = _auth(cliente, "ana", cenario["e1"])  # gerente sem acesso.empresas
    assert cliente.get("/empresas", headers=ana).status_code == 403


def test_criar_e_alterar(cliente, cenario, admin, anapolis):
    dados = {"codigo": "04", "nome": "Nova Loja", "cnpj": "11.222.333/0001-81", "cep": "75110-010",
             "cidade_id": anapolis, "bairro": "Jundiaí", "crt": "1", "sped_perfil": "A", "sped_atividade": "1"}
    r = cliente.post("/empresas", headers=admin, json=dados)
    assert r.status_code == 201, r.text
    criada = r.json()
    assert (criada["cnpj"], criada["cep"], criada["cidade"]["nome"]) == (CNPJ, "75110010", "Anápolis")
    assert criada["tema"] == tema_automatico("04") and criada["imagens"] == []

    # o código não muda, mesmo se vier no corpo
    r = cliente.put(f"/empresas/{criada['id']}", headers=admin,
                    json={**dados, "codigo": "09", "nome": "Loja Nova", "tema": {**TEMA, "principal": "#941D70"}})
    assert r.status_code == 200, r.text
    assert (r.json()["codigo"], r.json()["nome"], r.json()["tema"]) == ("04", "Loja Nova", TEMA)


def test_regras(cliente, cenario, admin):
    def criar(**extra):
        return cliente.post("/empresas", headers=admin, json={"codigo": "05", "nome": "Loja", **extra})

    assert criar(codigo="01").status_code == 409  # código já usado
    assert criar(codigo="5").status_code == 422
    assert criar(cnpj="11222333000100").json()["detail"] == "CNPJ inválido"
    assert criar(cidade_id=999).status_code == 422
    assert criar(tema={**TEMA, "fundo": "azul"}).status_code == 422
    assert criar(cnpj=CNPJ).status_code == 201
    r = cliente.post("/empresas", headers=admin, json={"codigo": "06", "nome": "Outra", "cnpj": CNPJ})
    assert (r.status_code, r.json()["detail"]) == (409, "O CNPJ já é da empresa 05 - Loja")


def test_login_traz_o_tema_escolhido(cliente, cenario, admin):
    cliente.put(f"/empresas/{cenario['e2']}", headers=admin, json={"nome": "Loja Bairro", "tema": TEMA})
    corpo = cliente.post("/auth/login", json={"login": "bia", "senha": "senha-bia"}).json()
    temas = {e["codigo"]: e["tema"] for e in corpo["empresas"]}
    assert temas == {"01": tema_automatico("01"), "02": TEMA}


def test_imagens(cliente, cenario, admin):
    url = f"/empresas/{cenario['e1']}/imagens"
    assert cliente.get(f"{url}/logo", headers=admin).status_code == 404

    r = cliente.put(f"{url}/logo", headers={**admin, "Content-Type": "image/png"}, content=PNG)
    assert r.status_code == 200, r.text
    assert r.json()["imagens"] == ["logo"]
    cliente.put(f"{url}/qrcode", headers={**admin, "Content-Type": "image/jpeg"}, content=JPEG)

    # qualquer usuário logado vê as imagens (vão nos relatórios e boletos)
    bia = _auth(cliente, "bia", cenario["e1"])
    r = cliente.get(f"{url}/qrcode", headers=bia)
    assert (r.status_code, r.headers["content-type"], r.content) == (200, "image/jpeg", JPEG)
    assert cliente.put(f"{url}/logo", headers=bia, content=PNG).status_code == 403

    assert cliente.put(f"{url}/logo", headers=admin, content=b"<svg></svg>").json()["detail"] == "Envie uma imagem PNG ou JPEG"
    assert cliente.put(f"{url}/logo", headers=admin, content=PNG + b"\x00" * 1024 * 1024).status_code == 422
    assert cliente.put(f"{url}/foto", headers=admin, content=PNG).status_code == 404

    r = cliente.delete(f"{url}/logo", headers=admin)
    assert r.json()["imagens"] == ["qrcode"]
    assert cliente.get(f"{url}/logo", headers=admin).status_code == 404
