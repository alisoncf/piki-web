"""Cadastro de clientes, setores, cobradores, cidades, órgãos e grupos. Dados fictícios (CPF e CNPJ gerados só para teste)."""
import pytest

from app.dominios.cidades.modelos import Cidade, nome_de_busca
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


@pytest.fixture
def cidades(banco):
    """Algumas cidades do IBGE (a lista completa vem na migração, que os testes não rodam)."""
    with banco() as db:
        lista = [Cidade(codigo_ibge=c, nome=n, uf=u, nome_busca=nome_de_busca(n)) for c, n, u in [
            ("5201108", "Anápolis", "GO"), ("5208707", "Goiânia", "GO"), ("3525904", "Jundiaí", "SP"),
            ("5201405", "Aparecida de Goiânia", "GO"),
        ]]
        db.add_all(lista)
        db.commit()
        return {c.nome: c.id for c in lista}


def _dados(**extra):
    return {"nome": "Maria Teste", "cpf_cnpj": "529.982.247-25", **extra}


def test_cnpj_valido():
    assert cnpj_valido(CNPJ_A)
    assert not cnpj_valido("11222333000182")
    assert not cnpj_valido("11111111111111")


def test_criar_e_consultar_cliente(cliente, cenario, admin, cidades):
    grupo = cliente.post("/grupos-clientes", json={"nome": "Servidor municipal"}, headers=admin).json()
    setor = cliente.post("/setores", json={"nome": "Jundiaí", "cidade_id": cidades["Anápolis"]}, headers=admin).json()
    orgao = cliente.post("/orgaos", json={"nome": "Escola Modelo", "grupo_id": grupo["id"]}, headers=admin).json()
    irma = cliente.post("/parentescos", json={"nome": "Irmã"}, headers=admin).json()
    r = cliente.post("/clientes", headers=admin, json=_dados(
        setor_id=setor["id"], orgao_id=orgao["id"], grupo_id=grupo["id"], uf="go", cep="75.110-000",
        limite_credito="550.00", bloqueado=True, forma_cobranca="trabalho",
        telefones=[{"numero": "(62) 99999-0000", "tipo": "3"}],
        referencias=[{"nome": "Joana", "telefone": "62 3333-4444", "parentesco_id": irma["id"]}],
    ))
    assert r.status_code == 201, r.text
    criado = r.json()
    assert criado["cpf_cnpj"] == CPF_A
    assert criado["uf"] == "GO"
    assert criado["cep"] == "75110000"
    assert criado["limite_credito"] == "550.00"
    assert criado["setor"]["nome"] == "Jundiaí"
    assert criado["setor"]["cidade"]["nome"] == "Anápolis"
    assert criado["orgao"]["nome"] == "Escola Modelo"
    assert criado["empresa_cadastro"]["codigo"] == "01"
    assert criado["telefones"] == [{"numero": "62999990000", "tipo": "3"}]
    assert criado["referencias"] == [{"nome": "Joana", "telefone": "6233334444", "parentesco_id": irma["id"],
                                      "parentesco": {"id": irma["id"], "nome": "Irmã", "ativo": True}}]
    assert criado["bloqueado"] is True
    assert criado["forma_cobranca"] == "trabalho"
    assert criado["data_alteracao"] is not None

    assert cliente.get(f"/clientes/{criado['id']}", headers=admin).json() == criado


def test_forma_de_cobranca_e_parentesco_validos(cliente, cenario, admin):
    assert cliente.post("/clientes", headers=admin, json=_dados(forma_cobranca="1")).status_code == 422
    r = cliente.post("/clientes", headers=admin, json=_dados(referencias=[{"nome": "X", "parentesco_id": 999}]))
    assert r.status_code == 422
    assert r.json()["detail"] == "Parentesco não encontrado"
    assert cliente.post("/parentescos", headers=admin, json={"nome": "Tio"}).status_code == 201
    assert cliente.post("/parentescos", headers=admin, json={"nome": "TIO"}).status_code == 409
    assert [p["nome"] for p in cliente.get("/parentescos", headers=admin).json()] == ["Tio"]


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


def test_buscar_cidades(cliente, cenario, admin, cidades):
    def nomes(**params):
        return [c["nome"] for c in cliente.get("/cidades", headers=admin, params=params).json()]

    # sem ligar para acentos; quem começa com o termo vem antes
    assert nomes(busca="goiania") == ["Goiânia", "Aparecida de Goiânia"]
    assert nomes(busca="JUNDIAI") == ["Jundiaí"]
    assert nomes(busca="jundiai", uf="go") == []
    assert len(nomes()) == 4
    assert cliente.get("/cidades").status_code == 401


def test_setor_na_cidade_com_varios_cobradores(cliente, cenario, admin, cidades):
    um = cliente.post("/cobradores", headers=admin, json={"nome": "Sidnei"}).json()
    dois = cliente.post("/cobradores", headers=admin, json={"nome": "Edmilson"}).json()
    assert cliente.post("/cobradores", headers=admin, json={"nome": "SIDNEI"}).status_code == 409

    r = cliente.post("/setores", headers=admin, json={
        "nome": "Centro", "cidade_id": cidades["Anápolis"], "cobradores": [um["id"], dois["id"], um["id"]]})
    assert r.status_code == 201, r.text
    centro = r.json()
    assert centro["cidade"] == {"id": cidades["Anápolis"], "codigo_ibge": "5201108", "nome": "Anápolis", "uf": "GO"}
    assert [c["nome"] for c in centro["cobradores"]] == ["Edmilson", "Sidnei"]

    # um cobrador em vários setores
    r = cliente.post("/setores", headers=admin, json={"nome": "Jundiaí", "cidade_id": cidades["Anápolis"],
                                                      "cobradores": [um["id"]]})
    assert r.status_code == 201, r.text

    r = cliente.put(f"/setores/{centro['id']}", headers=admin, json={
        "nome": "Centro", "cidade_id": cidades["Anápolis"], "cobradores": [dois["id"]]})
    assert [c["nome"] for c in r.json()["cobradores"]] == ["Edmilson"]

    # o mesmo cobrador, visto de outra loja
    outra = _auth(cliente, "caio", cenario["e2"])
    assert [c["nome"] for c in cliente.get("/setores", headers=outra).json()[1]["cobradores"]] == ["Sidnei"]

    assert cliente.post("/setores", headers=admin, json={"nome": "Norte"}).status_code == 422  # sem cidade
    assert cliente.post("/setores", headers=admin, json={"nome": "Norte", "cidade_id": cidades["Goiânia"],
                                                         "cobradores": [999]}).status_code == 422
    assert cliente.post("/setores", headers=admin, json={"nome": "Norte", "cidade_id": 999}).status_code == 422
    # mesmo nome em outra cidade é outro setor; na mesma cidade, não
    assert cliente.post("/setores", headers=admin, json={"nome": "centro", "cidade_id": cidades["Goiânia"]}).status_code == 201
    assert cliente.post("/setores", headers=admin, json={"nome": "centro", "cidade_id": cidades["Anápolis"]}).status_code == 409


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
