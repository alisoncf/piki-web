"""Crediário na venda: limite do cliente, entrada, parcelas e carnê (D26). Dados fictícios."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.dominios.acesso import repositorio
from app.dominios.clientes.modelos import Cliente
from app.dominios.receber import servico as contas
from tests.test_vendas import admin, loja  # noqa: F401  (fixtures)


@pytest.fixture
def freguesa(banco, cenario):
    """Limite de 500, com 200 em aberto num carnê da outra loja; e uma cliente bloqueada."""
    with banco() as db:
        c = Cliente(nome="Freguesa Ficticia", cpf_cnpj="00000000191", limite_credito=Decimal("500.00"),
                    logradouro="Rua Ficticia", numero="10", cep="74000000")
        bloqueada = Cliente(nome="Bloqueada Ficticia", limite_credito=Decimal("1000.00"), bloqueado=True)
        db.add_all([c, bloqueada])
        db.flush()
        caio = repositorio.usuario_por_login(db, "caio")
        contas.lancar_carne(db, cenario["e2"], c.id, None, Decimal("200.00"), 2, date.today(), 30, "Antiga", caio.id)
        db.commit()
        return {"id": c.id, "bloqueada": bloqueada.id}


def _venda_no_crediario(cliente, loja, cliente_id, lencois, parcelas=3):  # noqa: F811
    davi = loja["davi"]
    url = f"/vendas/{cliente.post('/vendas', headers=davi).json()['id']}"
    cliente.post(f"{url}/itens", headers=davi, json={"produto_id": loja["produtos"]["lencol"], "quantidade": str(lencois)})
    r = cliente.put(url, headers=davi, json={"cliente_id": cliente_id, "forma_pagamento_id": loja["formas"]["crediario"],
                                             "parcelas": parcelas})
    assert r.status_code == 200, r.text
    assert cliente.post(f"{url}/fechar", headers=davi).status_code == 200
    return url, r.json()


def test_crediario_com_entrada_dentro_do_limite(cliente, loja, admin, freguesa):  # noqa: F811
    davi = loja["davi"]
    url, venda = _venda_no_crediario(cliente, loja, freguesa["id"], 4)
    assert venda["total"] == "400.00"
    assert venda["credito"] == {"limite": "500.00", "em_aberto": "200.00", "disponivel": "300.00", "em_prejuizo": "0.00",
                                "impedimento": None}

    # 400 a prazo passa dos 300 disponíveis, e o davi não tem vendas.autorizar
    receber = {"sessao_caixa_id": loja["sessao"]}
    r = cliente.post(f"{url}/receber", headers=davi, json=receber)
    assert r.status_code == 403 and r.headers["x-pede-autorizacao"] == "sim"
    assert r.json()["detail"] == ("O crediário de R$ 400,00 passa do limite disponível do cliente (R$ 300,00). "
                                  "Peça a autorização da gerência.")

    # com a entrada à vista (um pouco no dinheiro, um pouco no cartão), o resto cabe
    f = loja["formas"]
    no_crediario = [{"forma_pagamento_id": f["crediario"], "valor": "100.01"}]
    r = cliente.post(f"{url}/receber", headers=davi, json=receber | {"pagamentos": no_crediario})
    assert r.status_code == 422 and "não entra como pagamento à vista" in r.json()["detail"]
    entrada = [{"forma_pagamento_id": f["dinheiro"], "valor": "50.01"}, {"forma_pagamento_id": f["cartao_credito"], "valor": "50.00"}]
    r = cliente.post(f"{url}/receber", headers=davi, json=receber | {"pagamentos": entrada, "valor_recebido": "100"})
    assert r.status_code == 200, r.text
    venda = r.json()
    assert (venda["situacao"], venda["a_prazo"], venda["troco"], venda["data_base"]) == (
        "recebida", "299.99", "49.99", date.today().isoformat())
    assert [(p["forma_pagamento"]["nome"], p["valor"]) for p in venda["pagamentos"]] == [
        ("Dinheiro", "50.01"), ("Cartão de crédito", "50.00")]
    assert venda["limite_autorizado_por"] is None and venda["credito"] is None
    vencimentos = [contas.somar_meses(date.today(), i).isoformat() for i in (1, 2, 3)]
    assert [(p["numero"], p["vencimento"], p["valor"]) for p in venda["carne"]["parcelas"]] == [
        (1, vencimentos[0], "99.99"), (2, vencimentos[1], "99.99"),
        (3, vencimentos[2], "100.01"),  # os centavos que sobram vão na última
    ]

    # no caixa: o crediário e a entrada, cada um na sua forma
    sessao = cliente.get(f"/caixas/sessoes/{loja['sessao']}", headers=admin).json()
    assert sorted((x["forma_pagamento"]["nome"], x["valor"]) for x in sessao["lancamentos"]) == [
        ("Cartão de crédito", "50.00"), ("Crediário", "299.99"), ("Dinheiro", "50.01")]

    carne = cliente.get(f"{url}/carne", headers=davi).json()
    assert carne["cliente"] == {"id": freguesa["id"], "nome": "Freguesa Ficticia", "cpf_cnpj": "00000000191",
                                "endereco": "Rua Ficticia nº 10 - CEP 74000000", "cidade": ""}
    assert (carne["loja"]["nome"], carne["venda"], carne["carne"]["valor"]) == ("Loja Centro", venda["numero"], "299.99")

    # agora o que está em aberto soma as duas lojas
    _, outra = _venda_no_crediario(cliente, loja, freguesa["id"], 1)
    assert (outra["credito"]["em_aberto"], outra["credito"]["disponivel"]) == ("499.99", "0.01")


def test_crediario_acima_do_limite_com_autorizacao(cliente, loja, freguesa):  # noqa: F811
    davi = loja["davi"]
    url, _ = _venda_no_crediario(cliente, loja, freguesa["id"], 4, parcelas=2)
    pedido = {"sessao_caixa_id": loja["sessao"], "data_base": (date.today() - timedelta(days=40)).isoformat()}
    r = cliente.post(f"{url}/receber", headers=davi, json=pedido)
    assert r.status_code == 422 and "mais de um mês atrás" in r.json()["detail"]

    # a data base pode ser outra que não hoje; a 1ª parcela vence um mês depois dela
    base = date.today() - timedelta(days=10)
    pedido["data_base"] = base.isoformat()
    pedido["tipo_cobranca"] = "boleto"  # o cliente escolhe na hora
    r = cliente.post(f"{url}/receber", headers=davi, json=pedido | {"autorizacao": {"login": "ana", "senha": "senha-ana"}})
    assert r.status_code == 403 and "Ana Lima não pode" in r.json()["detail"]
    r = cliente.post(f"{url}/receber", headers=davi, json=pedido | {"autorizacao": {"login": "caio", "senha": "senha-caio"}})
    assert r.status_code == 200, r.text
    venda = r.json()
    assert (venda["limite_autorizado_por"]["nome"], venda["pagamentos"], venda["troco"]) == ("Caio Admin", [], None)
    assert [p["vencimento"] for p in venda["carne"]["parcelas"]] == [
        contas.somar_meses(base, 1).isoformat(), contas.somar_meses(base, 2).isoformat()]


def test_tipo_de_cobranca_vem_da_ficha_do_cliente_ou_da_escolha(banco, cliente, loja, admin, freguesa):  # noqa: F811
    url, _ = _venda_no_crediario(cliente, loja, freguesa["id"], 1)
    r = cliente.post(f"{url}/receber", headers=admin, json={"sessao_caixa_id": loja["sessao"]})
    assert r.status_code == 200, r.text
    with banco() as db:
        conta = contas.conta_da_venda(db, r.json()["id"])
        assert {p.tipo_cobranca for p in conta.parcelas} == {"cliente"}  # a ficha diz cobrança em domicílio
    url, _ = _venda_no_crediario(cliente, loja, freguesa["id"], 1)
    r = cliente.post(f"{url}/receber", headers=admin, json={"sessao_caixa_id": loja["sessao"], "tipo_cobranca": "loja"})
    filtrado = cliente.get("/receber/parcelas", headers=admin, params={"tipo_cobranca": "loja"}).json()
    assert {p["tipo_cobranca"] for p in filtrado["itens"]} == {"loja"} and filtrado["total"] == 3


def test_cliente_bloqueado_nao_compra_no_crediario(cliente, loja, freguesa):  # noqa: F811
    url, venda = _venda_no_crediario(cliente, loja, freguesa["bloqueada"], 1)
    assert venda["credito"]["impedimento"] == "O cliente está bloqueado e não pode comprar no crediário"
    r = cliente.post(f"{url}/receber", headers=loja["davi"],
                     json={"sessao_caixa_id": loja["sessao"], "autorizacao": {"login": "caio", "senha": "senha-caio"}})
    assert r.status_code == 422 and "bloqueado" in r.json()["detail"]


def test_vencimentos_e_divisao():
    assert contas.vencimentos(date(2026, 1, 31), 3, 30) == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)]
    assert contas.vencimentos(date(2026, 11, 30), 3, 30) == [date(2026, 11, 30), date(2026, 12, 30), date(2027, 1, 30)]
    assert contas.vencimentos(date(2026, 1, 1), 3, 15) == [date(2026, 1, 1), date(2026, 1, 16), date(2026, 1, 31)]
    assert contas.dividir(Decimal("100.00"), 3) == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    assert contas.dividir(Decimal("50.00"), 1) == [Decimal("50.00")]
