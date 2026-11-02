"""Cadastro de produtos, seções e marcas (D24). Dados fictícios; fotos numa pasta temporária."""
import pytest

from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.empresas.modelos import Empresa
from app.main import app
from app.nucleo import arquivos
from app.nucleo.arquivos import Pasta

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 50
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 50


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    return _auth(cliente, "caio", cenario["e1"])


@pytest.fixture
def cadastro(banco, cliente, cenario):
    """O davi cadastra produtos na empresa 01, mas não mexe em preço."""
    with banco() as db:
        perfil = acesso.criar_perfil(db, "Cadastro", ["produtos.ver", "produtos.editar"])
        davi = repositorio.usuario_por_login(db, "davi")
        acesso.dar_acesso(db, davi, db.get(Empresa, cenario["e1"]), perfil)
    return _auth(cliente, "davi", cenario["e1"])


@pytest.fixture
def pasta(tmp_path):
    armazenamento = Pasta(tmp_path)
    app.dependency_overrides[arquivos.armazenamento] = lambda: armazenamento
    yield tmp_path
    app.dependency_overrides.pop(arquivos.armazenamento, None)


@pytest.fixture
def base(cliente, admin):
    """Seção Cama com a subseção Jogo de cama, a marca Fictícia e um fornecedor."""
    cama = cliente.post("/secoes", headers=admin, json={"nome": "Cama"}).json()
    jogo = cliente.post("/subsecoes", headers=admin, json={"nome": "Jogo de cama", "secao_id": cama["id"]}).json()
    marca = cliente.post("/marcas", headers=admin, json={"nome": "Fictícia"}).json()
    fornecedor = cliente.post("/fornecedores", headers=admin,
                              json={"nome": "Tecidos Fictícios Ltda", "cpf_cnpj": "11222333000181"}).json()
    return {"secao": cama["id"], "subsecao": jogo["id"], "marca": marca["id"], "fornecedor": fornecedor["id"]}


def _produto(base, **extra):
    return {"nome": "JOGO DE CAMA CASAL 04 PCS TRENTO FICTICIA", "subsecao_id": base["subsecao"], **extra}


def test_criar_alterar_e_buscar(cliente, admin, base):
    r = cliente.post("/produtos", headers=admin, json=_produto(
        base, marca_id=base["marca"], unidade="un", custo="50.00", margem="100", preco_venda="119.90",
        preco_queima="89.90", ncm="6302.31.00", codigos_barras=["789 1234 567895"],
        fornecedores=[{"fornecedor_id": base["fornecedor"], "codigo": "TR-04"}]))
    assert r.status_code == 201, r.text
    p = r.json()
    assert (p["codigo"], p["unidade"], p["ncm"], p["codigos_barras"], p["preco_queima"]) == (
        1, "UN", "63023100", ["7891234567895"], "89.90")
    assert p["subsecao"]["secao"]["nome"] == "Cama" and p["marca"]["nome"] == "Fictícia"
    assert p["fornecedores"][0]["fornecedor"]["nome"] == "Tecidos Fictícios Ltda"

    r = cliente.post("/produtos", headers=admin, json=_produto(base, nome="TOALHA DE MESA 1.40X1.40", preco_venda="40"))
    assert r.json()["codigo"] == 2  # o seguinte ao maior
    outro = r.json()["id"]

    def busca(**params):
        return [i["codigo"] for i in cliente.get("/produtos", headers=admin, params=params).json()["itens"]]

    assert busca(busca="trento casal") == [1]  # todas as palavras, em qualquer ordem
    assert busca(busca="2") == [2]  # pelo código
    assert busca(busca="7891234567895") == [1]  # pelo código de barras
    assert busca(busca="tr-04") == [1]  # pelo código do fornecedor
    assert busca(secao_id=base["secao"]) == [1, 2]
    assert busca(fornecedor_id=base["fornecedor"]) == [1]
    resumo = cliente.get("/produtos", headers=admin, params={"busca": "trento"}).json()["itens"][0]
    assert (resumo["fornecedor"], resumo["foto_id"]) == ("Tecidos Fictícios Ltda", None)

    # código de barras de outro produto
    r = cliente.put(f"/produtos/{outro}", headers=admin, json=_produto(base, nome="TOALHA", codigos_barras=["7891234567895"]))
    assert r.status_code == 409 and "00000001" not in r.json()["detail"] and "1 - JOGO" in r.json()["detail"]
    r = cliente.put(f"/produtos/{outro}", headers=admin, json=_produto(base, nome="TOALHA", ativo=False, preco_venda="40"))
    assert r.status_code == 200 and not r.json()["ativo"]
    assert busca(ativo=True) == [1]


@pytest.mark.parametrize("extra, mensagem", [
    ({"preco_venda": "50", "preco_queima": "50"}, "queima"),
    ({"codigos_barras": ["1234567"]}, "Código de barras inválido"),
    ({"codigos_barras": ["78912345", "78912345"]}, "repetido"),
    ({"subsecao_id": 999}, "Subseção"),
])
def test_dados_invalidos(cliente, admin, base, extra, mensagem):
    r = cliente.post("/produtos", headers=admin, json=_produto(base, **extra))
    assert r.status_code == 422 and mensagem in r.json()["detail"]


def test_preco_pede_permissao(cliente, admin, cadastro, base):
    r = cliente.post("/produtos", headers=cadastro, json=_produto(base, preco_venda="10"))
    assert r.status_code == 403 and "produtos.precos" in r.json()["detail"]
    r = cliente.post("/produtos", headers=cadastro, json=_produto(base))
    assert r.status_code == 201 and r.json()["preco_venda"] == "0.00"
    produto = r.json()["id"]

    # quem tem a permissão põe o preço; quem não tem altera o resto sem mexer nele
    cliente.put(f"/produtos/{produto}", headers=admin, json=_produto(base, custo="30", preco_venda="79.90"))
    r = cliente.put(f"/produtos/{produto}", headers=cadastro,
                    json=_produto(base, nome="JOGO DE CAMA NOVO", custo="30", preco_venda="79.90"))
    assert r.status_code == 200 and r.json()["nome"] == "JOGO DE CAMA NOVO"
    r = cliente.put(f"/produtos/{produto}", headers=cadastro, json=_produto(base, custo="30", preco_venda="59.90"))
    assert r.status_code == 403
    assert cliente.post("/secoes", headers=cadastro, json={"nome": "Mesa"}).status_code == 201


def test_fotos(cliente, admin, base, pasta):
    produto = cliente.post("/produtos", headers=admin, json=_produto(base)).json()["id"]
    url = f"/produtos/{produto}/fotos"
    assert cliente.post(url, headers=admin, content=b"%PDF-1.4").status_code == 422
    primeira = cliente.post(url, headers=admin, content=JPEG).json()["id"]
    segunda = cliente.post(url, headers=admin, content=PNG).json()["id"]
    assert len(list(pasta.rglob("*.*"))) == 2

    r = cliente.get(f"{url}/{segunda}/arquivo", headers=admin)
    assert r.content == PNG and r.headers["content-type"] == "image/png"
    assert cliente.get("/produtos", headers=admin).json()["itens"][0]["foto_id"] == primeira

    r = cliente.post(f"{url}/{segunda}/principal", headers=admin)
    assert [f["id"] for f in r.json()] == [segunda, primeira]
    assert [f["id"] for f in cliente.get(f"/produtos/{produto}", headers=admin).json()["fotos"]] == [segunda, primeira]

    assert cliente.delete(f"{url}/{segunda}", headers=admin).status_code == 204
    assert [f["id"] for f in cliente.get(f"/produtos/{produto}", headers=admin).json()["fotos"]] == [primeira]
    assert cliente.get(f"{url}/{segunda}/arquivo", headers=admin).status_code == 404


def test_secoes_e_marcas(cliente, admin, base):
    assert cliente.post("/secoes", headers=admin, json={"nome": "cama"}).status_code == 409
    mesa = cliente.post("/secoes", headers=admin, json={"nome": "Mesa"}).json()["id"]
    # a subseção muda de seção
    r = cliente.put(f"/subsecoes/{base['subsecao']}", headers=admin, json={"nome": "Jogo de cama", "secao_id": mesa})
    assert r.status_code == 200 and r.json()["secao"]["nome"] == "Mesa"
    secoes = {s["nome"]: [x["nome"] for x in s["subsecoes"]] for s in cliente.get("/secoes", headers=admin).json()}
    assert secoes == {"Cama": [], "Mesa": ["Jogo de cama"]}
    assert cliente.post("/marcas", headers=admin, json={"nome": "FICTÍCIA"}).status_code == 409  # maiúsculas não contam
    assert cliente.post("/marcas", headers=admin, json={"nome": "Ficticia"}).status_code == 201  # acento conta
    r = cliente.put(f"/marcas/{base['marca']}", headers=admin, json={"nome": "Fictícia", "ativo": False})
    assert r.json()["ativo"] is False


def test_sem_permissao(cliente, cenario):
    ana = _auth(cliente, "ana", cenario["e1"])
    assert cliente.get("/produtos", headers=ana).status_code == 403
