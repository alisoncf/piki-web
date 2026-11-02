"""Cadastro de fornecedores e consulta de CNPJ (D22). Dados fictícios; a BrasilAPI é simulada: os testes não usam a rede."""
import pytest

from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.fornecedores import brasilapi
from app.nucleo.textos import nome_proprio

CNPJ_A = "11222333000181"
CNPJ_B = "11444777000161"
CPF = "52998224725"

# como a BrasilAPI responde (campos que a ficha usa)
RECEITA = {
    "cnpj": CNPJ_A, "razao_social": "TECIDOS FICTICIOS LTDA", "nome_fantasia": "FICTICIA TEXTIL",
    "descricao_situacao_cadastral": "ATIVA", "cep": "89010000", "descricao_tipo_de_logradouro": "RUA",
    "logradouro": "DAS FLORES", "numero": "100", "complemento": "", "bairro": "CENTRO", "municipio": "BLUMENAU",
    "uf": "SC", "codigo_municipio_ibge": 4202404, "ddd_telefone_1": "4733334444", "ddd_telefone_2": "",
    "email": "Vendas@Ficticia.com.br",
}


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    return _auth(cliente, "caio", cenario["e1"])


@pytest.fixture
def blumenau(banco):
    with banco() as db:
        cidade = Cidade(codigo_ibge="4202404", nome="Blumenau", uf="SC", nome_busca=nome_de_busca("Blumenau"))
        db.add(cidade)
        db.commit()
        return cidade.id


@pytest.fixture
def receita(monkeypatch):
    """Troca a consulta à BrasilAPI por um dicionário cnpj -> resposta."""
    respostas: dict = {}

    def consultar(cnpj):
        resposta = respostas.get(cnpj)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    monkeypatch.setattr(brasilapi, "consultar", consultar)
    return respostas


def _dados(**extra):
    return {"nome": "Tecidos Fictícios Ltda", "cpf_cnpj": "11.222.333/0001-81", **extra}


def test_criar_consultar_e_alterar(cliente, admin, blumenau):
    r = cliente.post("/fornecedores", headers=admin, json=_dados(
        nome_fantasia="Fictícia Têxtil", cep="89010-000", cidade_id=blumenau, bairro="Centro",
        telefones=[{"numero": "(47) 3333-4444", "tipo": "2"}],
        contatos=[{"nome": "Rita", "funcao": "Representante", "telefone": "(62) 99999-0000", "email": " "},
                  {"nome": "Financeiro", "email": "financeiro@ficticia.com.br"}],
    ))
    assert r.status_code == 201, r.text
    criado = r.json()
    assert (criado["cpf_cnpj"], criado["tipo"], criado["cep"]) == (CNPJ_A, "J", "89010000")
    assert criado["cidade"]["nome"] == "Blumenau"
    assert criado["telefones"] == [{"numero": "4733334444", "tipo": "2"}]
    assert criado["contatos"] == [
        {"nome": "Rita", "funcao": "Representante", "telefone": "62999990000", "email": None},
        {"nome": "Financeiro", "funcao": None, "telefone": None, "email": "financeiro@ficticia.com.br"},
    ]
    assert cliente.get(f"/fornecedores/{criado['id']}", headers=admin).json() == criado

    # telefones e contatos enviados substituem os anteriores
    r = cliente.put(f"/fornecedores/{criado['id']}", headers=admin, json=_dados(contatos=[{"nome": "Rita"}]))
    assert r.status_code == 200, r.text
    assert (r.json()["telefones"], [c["nome"] for c in r.json()["contatos"]]) == ([], ["Rita"])


def test_documento_obrigatorio_valido_e_unico(cliente, admin):
    for doc in ("", "11222333000182", "123"):
        r = cliente.post("/fornecedores", headers=admin, json=_dados(cpf_cnpj=doc))
        assert r.status_code == 422, doc
    r = cliente.post("/fornecedores", headers=admin, json=_dados(nome="Costureira Fictícia", cpf_cnpj=CPF))
    assert (r.status_code, r.json()["tipo"]) == (201, "F")  # pessoa física também fornece

    assert cliente.post("/fornecedores", headers=admin, json=_dados()).status_code == 201
    r = cliente.post("/fornecedores", headers=admin, json=_dados(nome="Outro Nome"))
    assert r.status_code == 409
    assert "Tecidos Fictícios Ltda" in r.json()["detail"]


def test_lista_busca_por_nome_fantasia_contato_e_cnpj(cliente, admin):
    cliente.post("/fornecedores", headers=admin, json=_dados(nome_fantasia="Fictícia Têxtil", contatos=[{"nome": "Rita"}]))
    cliente.post("/fornecedores", headers=admin, json=_dados(nome="Toalhas Exemplo SA", cpf_cnpj=CNPJ_B, ativo=False))

    def nomes(**params):
        return [f["nome"] for f in cliente.get("/fornecedores", headers=admin, params=params).json()]

    assert nomes() == ["Tecidos Fictícios Ltda", "Toalhas Exemplo SA"]
    assert nomes(busca="têxtil") == ["Tecidos Fictícios Ltda"]
    assert nomes(busca="rita") == ["Tecidos Fictícios Ltda"]
    assert nomes(busca="11.444") == ["Toalhas Exemplo SA"]
    assert nomes(so_ativos=True) == ["Tecidos Fictícios Ltda"]


def test_permissoes(cliente, cenario):
    # a ana (Gerente) só tem permissões de acesso
    ana = _auth(cliente, "ana", cenario["e1"])
    assert cliente.get("/fornecedores", headers=ana).status_code == 403
    assert cliente.post("/fornecedores", headers=ana, json=_dados()).status_code == 403
    assert cliente.get(f"/cnpj/{CNPJ_A}", headers=ana).status_code == 403


def test_consulta_cnpj_preenche_a_ficha(cliente, admin, blumenau, receita):
    receita[CNPJ_A] = RECEITA
    r = cliente.get("/cnpj/11.222.333.0001-81", headers=admin)  # a barra do CNPJ não cabe na URL
    assert r.status_code == 200, r.text
    assert r.json() == {
        "cnpj": CNPJ_A, "razao_social": "Tecidos Ficticios Ltda", "nome_fantasia": "Ficticia Textil",
        "situacao": "ATIVA", "cep": "89010000", "logradouro": "Rua das Flores", "numero": "100", "complemento": None,
        "bairro": "Centro", "cidade": {"id": blumenau, "codigo_ibge": "4202404", "nome": "Blumenau", "uf": "SC"},
        "telefones": ["4733334444"], "email": "vendas@ficticia.com.br", "fornecedor_id": None,
    }
    # já cadastrado: a ficha avisa em vez de criar outro
    criado = cliente.post("/fornecedores", headers=admin, json=_dados()).json()
    assert cliente.get(f"/cnpj/{CNPJ_A}", headers=admin).json()["fornecedor_id"] == criado["id"]


def test_consulta_cnpj_corta_no_tamanho_da_ficha(cliente, admin, receita):
    receita[CNPJ_A] = {**RECEITA, "complemento": "SALA " * 20}
    assert len(cliente.get(f"/cnpj/{CNPJ_A}", headers=admin).json()["complemento"]) <= 60


def test_consulta_cnpj_cidade_pelo_nome(cliente, admin, blumenau, receita):
    receita[CNPJ_A] = {**RECEITA, "codigo_municipio_ibge": None, "municipio": "BLUMENAU"}
    assert cliente.get(f"/cnpj/{CNPJ_A}", headers=admin).json()["cidade"]["id"] == blumenau


def test_consulta_cnpj_erros(cliente, admin, receita):
    assert cliente.get("/cnpj/11222333000182", headers=admin).status_code == 422  # dígito errado
    assert cliente.get(f"/cnpj/{CNPJ_B}", headers=admin).status_code == 404  # a Receita não conhece
    receita[CNPJ_A] = brasilapi.CnpjIndisponivel("fora do ar")
    r = cliente.get(f"/cnpj/{CNPJ_A}", headers=admin)
    assert r.status_code == 503
    assert "à mão" in r.json()["detail"]


def test_nome_proprio():
    assert nome_proprio("TECIDOS DA SILVA LTDA") == "Tecidos da Silva Ltda"
    assert nome_proprio("ABC COMERCIO DE TOALHAS EIRELI EPP") == "Abc Comercio de Toalhas EIRELI EPP"
    assert nome_proprio("FIACAO S.A.") == "Fiacao S.A."
    assert nome_proprio("SANTA BARBARA D'OESTE") == "Santa Barbara D'Oeste"
    assert nome_proprio("  Já Escrito  de Propósito ") == "Já Escrito de Propósito"
    assert nome_proprio("") is None

