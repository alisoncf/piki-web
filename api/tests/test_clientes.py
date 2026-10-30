"""Cadastro de clientes, setores, órgãos e grupos. Dados fictícios (CPF e CNPJ gerados só para teste)."""
import pytest

from app.nucleo.documentos import cnpj_valido

CPF_A = "52998224725"
CPF_B = "11144477735"
CNPJ_A = "11222333000181"


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    """Cabeçalho de um administrador (todas as permissões) na empresa 01."""
    return _auth(cliente, "caio", cenario["e1"])


def _dados(**extra):
    return {"nome": "Maria Teste", "cpf_cnpj": "529.982.247-25", **extra}


def test_cnpj_valido():
    assert cnpj_valido(CNPJ_A)
    assert not cnpj_valido("11222333000182")
    assert not cnpj_valido("11111111111111")


def test_criar_e_consultar_cliente(cliente, cenario, admin):
    grupo = cliente.post("/grupos-clientes", json={"nome": "Servidor municipal"}, headers=admin).json()
    setor = cliente.post("/setores", json={"nome": "Jundiaí", "cidade": "Anápolis", "uf": "go"}, headers=admin).json()
    orgao = cliente.post("/orgaos", json={"nome": "Escola Modelo", "grupo_id": grupo["id"]}, headers=admin).json()
    r = cliente.post("/clientes", headers=admin, json=_dados(
        setor_id=setor["id"], orgao_id=orgao["id"], grupo_id=grupo["id"], uf="go", cep="75.110-000",
        limite_credito="550.00", telefones=[{"numero": "(62) 99999-0000", "tipo": "3"}],
        referencias=[{"nome": "Loja Vizinha", "telefone": "62 3333-4444", "tipo": "1"}],
    ))
    assert r.status_code == 201, r.text
    criado = r.json()
    assert criado["cpf_cnpj"] == CPF_A
    assert criado["uf"] == "GO"
    assert criado["cep"] == "75110000"
    assert criado["limite_credito"] == "550.00"
    assert criado["setor"]["nome"] == "Jundiaí"
    assert criado["orgao"]["nome"] == "Escola Modelo"
    assert criado["empresa_cadastro"]["codigo"] == "01"
    assert criado["telefones"] == [{"numero": "62999990000", "tipo": "3"}]
    assert criado["referencias"] == [{"nome": "Loja Vizinha", "telefone": "6233334444", "tipo": "1"}]
    assert criado["data_alteracao"] is not None

    assert cliente.get(f"/clientes/{criado['id']}", headers=admin).json() == criado


def test_documento_invalido_ou_repetido(cliente, cenario, admin):
    r = cliente.post("/clientes", headers=admin, json=_dados(cpf_cnpj="52998224724"))
    assert r.status_code == 422
    assert r.json()["detail"] == "CPF inválido"
    # CNPJ só vale para pessoa jurídica
    assert cliente.post("/clientes", headers=admin, json=_dados(cpf_cnpj=CNPJ_A)).status_code == 422
    assert cliente.post("/clientes", headers=admin, json=_dados(tipo="J", cpf_cnpj=CNPJ_A)).status_code == 201

    cliente.post("/clientes", headers=admin, json=_dados())
    r = cliente.post("/clientes", headers=admin, json=_dados(nome="Outra Maria"))
    assert r.status_code == 409
    assert "Maria Teste" in r.json()["detail"]
    # sem documento, pode repetir o nome
    assert cliente.post("/clientes", headers=admin, json=_dados(cpf_cnpj=None)).status_code == 201


def test_alterar_substitui_telefones(cliente, cenario, admin):
    criado = cliente.post("/clientes", headers=admin, json=_dados(
        telefones=[{"numero": "6233334444", "tipo": "1"}])).json()
    r = cliente.put(f"/clientes/{criado['id']}", headers=admin, json=_dados(
        nome="Maria Alterada", telefones=[{"numero": "62988887777", "tipo": "3"}]))
    assert r.status_code == 200, r.text
    assert r.json()["nome"] == "Maria Alterada"
    assert r.json()["telefones"] == [{"numero": "62988887777", "tipo": "3"}]
    assert cliente.put("/clientes/999", headers=admin, json=_dados()).status_code == 404


def test_busca_paginada(cliente, cenario, admin):
    for i, nome in enumerate(["Ana Souza", "Bruna Souza", "Carla Lima"]):
        cliente.post("/clientes", headers=admin, json={
            "nome": nome, "telefones": [{"numero": f"6299999000{i}", "tipo": "3"}]})
    cliente.post("/clientes", headers=admin, json=_dados(nome="Dora Dias"))

    r = cliente.get("/clientes", headers=admin, params={"busca": "souza"}).json()
    assert r["total"] == 2
    assert [c["nome"] for c in r["itens"]] == ["Ana Souza", "Bruna Souza"]

    r = cliente.get("/clientes", headers=admin, params={"limite": 2, "deslocamento": 2}).json()
    assert r["total"] == 4
    assert [c["nome"] for c in r["itens"]] == ["Carla Lima", "Dora Dias"]

    assert cliente.get("/clientes", headers=admin, params={"busca": "529.982"}).json()["itens"][0]["nome"] == "Dora Dias"
    assert cliente.get("/clientes", headers=admin, params={"busca": "99990002"}).json()["itens"][0]["nome"] == "Carla Lima"


def test_anotacoes_registram_usuario_e_loja(cliente, cenario, admin):
    criado = cliente.post("/clientes", headers=admin, json=_dados()).json()
    r = cliente.post(f"/clientes/{criado['id']}/anotacoes", headers=admin, json={"texto": "  Prefere ligação à tarde  "})
    assert r.status_code == 201, r.text
    [anotacao] = r.json()["anotacoes"]
    assert anotacao["texto"] == "Prefere ligação à tarde"
    assert anotacao["usuario"]["nome"] == "Caio Admin"
    assert anotacao["empresa"]["codigo"] == "01"


def test_setor_com_um_cobrador_por_loja(cliente, cenario, admin):
    cobrador = cliente.post("/funcionarios", headers=admin, json={"nome": "Cobrador Um", "empresa_id": cenario["e1"]}).json()
    outro = cliente.post("/funcionarios", headers=admin, json={"nome": "Cobrador Dois", "empresa_id": cenario["e2"]}).json()
    r = cliente.post("/setores", headers=admin, json={"nome": "Centro", "cidade": "Anápolis", "cobradores": [
        {"empresa_id": cenario["e1"], "funcionario_id": cobrador["id"]},
        {"empresa_id": cenario["e2"], "funcionario_id": outro["id"]},
    ]})
    assert r.status_code == 201, r.text
    setor = r.json()
    assert {(c["empresa"]["codigo"], c["funcionario"]["nome"]) for c in setor["cobradores"]} == {
        ("01", "Cobrador Um"), ("02", "Cobrador Dois")}

    r = cliente.put(f"/setores/{setor['id']}", headers=admin, json={"nome": "Centro", "cidade": "Anápolis", "cobradores": [
        {"empresa_id": cenario["e1"], "funcionario_id": outro["id"]}]})
    assert r.status_code == 200, r.text
    assert [(c["empresa"]["codigo"], c["funcionario"]["nome"]) for c in r.json()["cobradores"]] == [("01", "Cobrador Dois")]

    r = cliente.post("/setores", headers=admin, json={"nome": "Norte", "cobradores": [
        {"empresa_id": cenario["e1"], "funcionario_id": cobrador["id"]},
        {"empresa_id": cenario["e1"], "funcionario_id": outro["id"]}]})
    assert r.status_code == 422
    # mesmo nome em outra cidade é outro setor; na mesma cidade, não
    assert cliente.post("/setores", headers=admin, json={"nome": "centro", "cidade": "Goiânia"}).status_code == 201
    assert cliente.post("/setores", headers=admin, json={"nome": "centro", "cidade": "anápolis"}).status_code == 409


def test_orgao_e_grupo_sem_repetir_nome(cliente, cenario, admin):
    assert cliente.post("/grupos-clientes", headers=admin, json={"nome": "Geral"}).status_code == 201
    assert cliente.post("/grupos-clientes", headers=admin, json={"nome": "GERAL"}).status_code == 409
    assert cliente.post("/orgaos", headers=admin, json={"nome": "Prefeitura"}).status_code == 201
    assert cliente.post("/orgaos", headers=admin, json={"nome": "prefeitura"}).status_code == 409
    assert [o["nome"] for o in cliente.get("/orgaos", headers=admin, params={"busca": "pref"}).json()] == ["Prefeitura"]


def test_permissoes(cliente, cenario):
    # bia tem só acesso.* na 01: não vê clientes
    bia = _auth(cliente, "bia", cenario["e1"])
    assert cliente.get("/clientes", headers=bia).status_code == 403
    assert cliente.post("/clientes", headers=bia, json=_dados()).status_code == 403
    assert cliente.get("/clientes").status_code == 401
