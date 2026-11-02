"""Estoque de cada loja (D24). Dados fictícios."""
from decimal import Decimal

import pytest

from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.empresas.modelos import Empresa
from app.dominios.estoque import servico


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    return _auth(cliente, "caio", cenario["e1"])


def _produto(cliente, cabecalho, **extra):
    cama = cliente.post("/secoes", headers=cabecalho, json={"nome": "Cama"}).json()
    sub = cliente.post("/subsecoes", headers=cabecalho, json={"nome": "Jogo de cama", "secao_id": cama["id"]}).json()
    r = cliente.post("/produtos", headers=cabecalho, json={"nome": "JOGO DE CAMA FICTICIO", "subsecao_id": sub["id"], **extra})
    return r.json()["id"]


def test_ajuste_e_historico(cliente, cenario, admin):
    produto = _produto(cliente, admin)
    url = f"/produtos/{produto}/estoque"
    # sem movimento, o saldo é zero
    assert cliente.get(url, headers=admin).json() == {
        "produto_id": produto, "quantidade": "0.000", "reservado": "0.000", "disponivel": "0.000",
        "localizacao": None, "cst_csosn": None, "cfop": None, "aliquota_icms": None}

    r = cliente.post(f"{url}/ajuste", headers=admin, json={"quantidade": "12", "motivo": "Contagem da prateleira"})
    assert r.status_code == 200 and r.json()["quantidade"] == "12.000"
    assert cliente.post(f"{url}/ajuste", headers=admin, json={"quantidade": "12", "motivo": "De novo"}).status_code == 422
    assert cliente.post(f"{url}/ajuste", headers=admin, json={"quantidade": "1.5", "motivo": "Fração"}).status_code == 422
    r = cliente.post(f"{url}/ajuste", headers=admin, json={"quantidade": "-2", "motivo": "Vendido sem baixa"})
    assert r.json()["quantidade"] == "-2.000"  # negativo é aceito

    movimentos = cliente.get(f"{url}/movimentos", headers=admin).json()
    assert movimentos["total"] == 2
    assert [(m["descricao"], m["quantidade"], m["saldo"], m["observacao"], m["usuario"]["nome"])
            for m in movimentos["itens"]] == [
        ("Ajuste", "-14.000", "-2.000", "Vendido sem baixa", "Caio Admin"),
        ("Ajuste", "12.000", "12.000", "Contagem da prateleira", "Caio Admin")]

    # cada loja tem o seu estoque
    outra = _auth(cliente, "caio", cenario["e2"])
    assert cliente.get(url, headers=outra).json()["quantidade"] == "0.000"
    assert cliente.get(f"{url}/movimentos", headers=outra).json()["total"] == 0
    lista = cliente.get("/produtos", headers=admin).json()["itens"]
    assert lista[0]["estoque"] == "-2.000"
    assert cliente.get("/produtos", headers=outra).json()["itens"][0]["estoque"] == "0.000"


def test_localizacao_e_impostos(cliente, admin):
    produto = _produto(cliente, admin)
    url = f"/produtos/{produto}/estoque"
    r = cliente.put(url, headers=admin, json={"localizacao": " Prateleira 3 ", "cst_csosn": "102", "cfop": "5.102",
                                              "aliquota_icms": "18"})
    assert r.status_code == 200, r.text
    assert (r.json()["localizacao"], r.json()["cfop"], r.json()["aliquota_icms"]) == ("Prateleira 3", "5102", "18.00")
    assert cliente.put(url, headers=admin, json={"cst_csosn": "1"}).status_code == 422


def test_movimentar_reserva_e_fracao(banco, cliente, cenario, admin):
    """O que as vendas e consignações vão usar: o reservado faz parte da quantidade, mas não está disponível."""
    produto = _produto(cliente, admin)
    with banco() as db:
        servico.movimentar(db, cenario["e1"], produto, "entrada", Decimal(10), documento="nota 1")
        servico.movimentar(db, cenario["e1"], produto, "consignacao_envio", reservado=Decimal(3))
        db.commit()
        estoque = servico.obter_estoque(db, cenario["e1"], produto)
        assert (estoque.quantidade, estoque.reservado, estoque.disponivel) == (10, 3, 7)
        with pytest.raises(servico.DadoInvalido, match="fração"):
            servico.movimentar(db, cenario["e1"], produto, "venda", Decimal("-0.5"))
        with pytest.raises(servico.DadoInvalido, match="desconhecido"):
            servico.movimentar(db, cenario["e1"], produto, "sumiu", Decimal(-1))


def test_permissoes(banco, cliente, cenario, admin):
    produto = _produto(cliente, admin)
    with banco() as db:
        perfil = acesso.criar_perfil(db, "Estoquista", ["produtos.ver", "estoque.ver"])
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "davi"), db.get(Empresa, cenario["e1"]), perfil)
    davi = _auth(cliente, "davi", cenario["e1"])
    url = f"/produtos/{produto}/estoque"
    assert cliente.get(url, headers=davi).status_code == 200
    assert cliente.put(url, headers=davi, json={}).status_code == 403
    assert cliente.post(f"{url}/ajuste", headers=davi, json={"quantidade": "1", "motivo": "Teste"}).status_code == 403
    ana = _auth(cliente, "ana", cenario["e1"])
    assert cliente.get(url, headers=ana).status_code == 403
