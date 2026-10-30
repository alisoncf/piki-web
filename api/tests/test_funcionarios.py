"""Cadastro de funcionários e cargos. Dados fictícios (CPFs gerados só para teste)."""
import pytest

from app.nucleo.documentos import cpf_valido

CPF_A = "52998224725"
CPF_B = "11144477735"


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    """Cabeçalho de um administrador (todas as permissões) na empresa 01."""
    return _auth(cliente, "caio", cenario["e1"])


def _dados(cenario, **extra):
    return {"nome": "Joana Teste", "apelido": "JOANA", "cpf": "529.982.247-25", "empresa_id": cenario["e1"], **extra}


def test_cpf_valido():
    assert cpf_valido(CPF_A)
    assert cpf_valido(CPF_B)
    assert not cpf_valido("52998224724")
    assert not cpf_valido("11111111111")
    assert not cpf_valido("123")


def test_criar_e_consultar_funcionario(cliente, cenario, admin):
    cargo = cliente.post("/cargos", json={"nome": "Vendedor", "vende": True}, headers=admin).json()
    r = cliente.post("/funcionarios", headers=admin, json=_dados(
        cenario, cargo_id=cargo["id"], uf="go", cep="75000-000", limite_vale="150.50",
        telefones=[{"numero": "(62) 99999-0000", "tipo": "3"}],
    ))
    assert r.status_code == 201, r.text
    criado = r.json()
    assert criado["cpf"] == CPF_A
    assert criado["uf"] == "GO"
    assert criado["cep"] == "75000000"
    assert criado["limite_vale"] == "150.50"
    assert criado["empresa"]["codigo"] == "01"
    assert criado["cargo"]["nome"] == "Vendedor"
    assert criado["telefones"] == [{"numero": "62999990000", "tipo": "3"}]

    lido = cliente.get(f"/funcionarios/{criado['id']}", headers=admin).json()
    assert lido == criado


def test_alterar_troca_lotacao_e_telefones(cliente, cenario, admin):
    criado = cliente.post("/funcionarios", headers=admin, json=_dados(
        cenario, telefones=[{"numero": "6233334444", "tipo": "1"}])).json()
    r = cliente.put(f"/funcionarios/{criado['id']}", headers=admin, json=_dados(
        cenario, empresa_id=cenario["e2"], telefones=[{"numero": "62988887777", "tipo": "3"}]))
    assert r.status_code == 200, r.text
    assert r.json()["empresa"]["codigo"] == "02"
    assert r.json()["telefones"] == [{"numero": "62988887777", "tipo": "3"}]


def test_cpf_invalido_e_duplicado(cliente, cenario, admin):
    r = cliente.post("/funcionarios", headers=admin, json=_dados(cenario, cpf="52998224724"))
    assert r.status_code == 422
    assert r.json()["detail"] == "CPF inválido"

    cliente.post("/funcionarios", headers=admin, json=_dados(cenario))
    r = cliente.post("/funcionarios", headers=admin, json=_dados(cenario, nome="Outra Pessoa"))
    assert r.status_code == 409
    assert "Joana Teste" in r.json()["detail"]


def test_sem_cpf_e_permitido(cliente, cenario, admin):
    # funcionários antigos do VB6 nem sempre têm CPF
    for nome in ("Sem CPF Um", "Sem CPF Dois"):
        assert cliente.post("/funcionarios", headers=admin, json=_dados(cenario, nome=nome, cpf="")).status_code == 201


def test_loja_e_cargo_precisam_existir(cliente, cenario, admin):
    assert cliente.post("/funcionarios", headers=admin, json=_dados(cenario, empresa_id=999)).status_code == 422
    assert cliente.post("/funcionarios", headers=admin, json=_dados(cenario, cargo_id=999)).status_code == 422


def test_telefone_invalido_ou_repetido(cliente, cenario, admin):
    tipo_errado = _dados(cenario, telefones=[{"numero": "62999990000", "tipo": "9"}])
    assert cliente.post("/funcionarios", headers=admin, json=tipo_errado).status_code == 422
    repetido = _dados(cenario, telefones=[{"numero": "62999990000", "tipo": "3"}, {"numero": "(62)99999-0000", "tipo": "1"}])
    r = cliente.post("/funcionarios", headers=admin, json=repetido)
    assert r.status_code == 422
    assert r.json()["detail"] == "Telefone repetido"


def test_busca_e_filtros(cliente, cenario, admin):
    cliente.post("/funcionarios", headers=admin, json=_dados(cenario))
    cliente.post("/funcionarios", headers=admin, json=_dados(
        cenario, nome="Pedro Teste", apelido="PEDRINHO", cpf=CPF_B, empresa_id=cenario["e2"], ativo=False))

    def nomes(**params):
        return [f["nome"] for f in cliente.get("/funcionarios", headers=admin, params=params).json()]

    assert nomes() == ["Joana Teste", "Pedro Teste"]
    assert nomes(busca="pedri") == ["Pedro Teste"]
    assert nomes(busca="529.982") == ["Joana Teste"]
    assert nomes(empresa_id=cenario["e2"]) == ["Pedro Teste"]
    assert nomes(so_ativos=True) == ["Joana Teste"]


def test_funcionario_inexistente(cliente, cenario, admin):
    assert cliente.get("/funcionarios/999", headers=admin).status_code == 404
    assert cliente.put("/funcionarios/999", headers=admin, json=_dados(cenario)).status_code == 404


def test_cargos(cliente, cenario, admin):
    r = cliente.post("/cargos", json={"nome": " Caixa "}, headers=admin)
    assert r.status_code == 201
    assert r.json() == {"id": r.json()["id"], "nome": "Caixa", "vende": False, "cobra": False, "ativo": True}
    assert cliente.post("/cargos", json={"nome": "CAIXA"}, headers=admin).status_code == 409
    alterado = cliente.put(f"/cargos/{r.json()['id']}", json={"nome": "Caixa", "cobra": True}, headers=admin).json()
    assert alterado["cobra"] is True
    assert [c["nome"] for c in cliente.get("/cargos", headers=admin).json()] == ["Caixa"]


def test_permissoes(cliente, cenario):
    # ana é Gerente na 01, perfil que só tem permissões de acesso
    ana = _auth(cliente, "ana", cenario["e1"])
    assert cliente.get("/funcionarios", headers=ana).status_code == 403
    assert cliente.get("/cargos", headers=ana).status_code == 403
    assert cliente.post("/funcionarios", headers=ana, json=_dados(cenario)).status_code == 403
