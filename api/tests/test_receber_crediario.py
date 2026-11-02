"""Recebimento das parcelas do crediário no caixa, em qualquer loja (D9, D26). Dados fictícios."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.dominios.acesso import repositorio
from app.dominios.caixa.modelos import FormaPagamento
from app.dominios.clientes.modelos import Cliente
from app.dominios.receber import servico as contas
from tests.test_vendas import admin, loja  # noqa: F401  (fixtures)


@pytest.fixture
def carnes(banco, cenario, loja):  # noqa: F811
    """Um carnê comprado na outra loja: uma parcela de 300 vencida há 20 dias e outra de 100 que vence daqui a 10."""
    with banco() as db:
        db.get(FormaPagamento, loja["formas"]["crediario"]).juros_atraso = Decimal("5.00")
        c = Cliente(nome="Freguesa Ficticia", limite_credito=Decimal("1000.00"))
        db.add(c)
        db.flush()
        caio = repositorio.usuario_por_login(db, "caio")
        vencida = contas.lancar_carne(db, cenario["e2"], c.id, None, Decimal("300.00"), 1, date.today() - timedelta(days=20),
                                      30, "Antiga", caio.id)
        a_vencer = contas.lancar_carne(db, cenario["e2"], c.id, None, Decimal("100.00"), 1, date.today() + timedelta(days=10),
                                       30, "Outra", caio.id)
        db.commit()
        return {"cliente": c.id, "vencida": vencida.parcelas[0].id, "a_vencer": a_vencer.parcelas[0].id}


def test_recebe_parcela_de_outra_loja_com_juros_sugeridos(cliente, loja, admin, carnes):  # noqa: F811
    davi, f = loja["davi"], loja["formas"]
    url = f"/crediario/clientes/{carnes['cliente']}/parcelas"
    abertas = cliente.get(url, headers=davi).json()
    assert abertas["juros_ao_mes"] == "5.00"
    # 5% ao mês, por dia: 300 × 5% ÷ 30 × 20 dias = 10,00; a que não venceu não tem juros
    assert [(p["loja"]["codigo"], p["aberto"], p["dias_atraso"], p["juros"]) for p in abertas["parcelas"]] == [
        ("02", "300.00", 20, "10.00"), ("02", "100.00", 0, "0.00")]

    # o caixa cobra menos juros (é só sugestão), paga uma parcela toda e parte da outra, em duas formas
    pedido = {
        "sessao_caixa_id": loja["sessao"], "cliente_id": carnes["cliente"], "valor_recebido": "120",
        "itens": [{"parcela_id": carnes["vencida"], "valor": "300.00", "juros": "8.00"},
                  {"parcela_id": carnes["a_vencer"], "valor": "150.00"}],
        "pagamentos": [{"forma_pagamento_id": f["dinheiro"], "valor": "100.00"},
                       {"forma_pagamento_id": f["cartao_credito"], "valor": "258.00"}],
    }
    r = cliente.post("/crediario/recebimentos", headers=davi, json=pedido)
    assert r.status_code == 422 and r.json()["detail"] == "Da parcela 1/1 faltam só R$ 100,00"
    pedido["itens"][1]["valor"] = "50.00"
    r = cliente.post("/crediario/recebimentos", headers=davi,
                     json=pedido | {"pagamentos": [{"forma_pagamento_id": f["crediario"], "valor": "358.00"}]})
    assert r.status_code == 422 and "não se paga com crediário" in r.json()["detail"]
    r = cliente.post("/crediario/recebimentos", headers=davi, json=pedido | {"pagamentos": pedido["pagamentos"][:1]})
    assert r.status_code == 422 and r.json()["detail"] == "Falta lançar R$ 258,00"
    r = cliente.post("/crediario/recebimentos", headers=davi, json=pedido)
    assert r.status_code == 201, r.text
    recebimento = r.json()
    assert (recebimento["empresa"]["codigo"], recebimento["total"], recebimento["troco"]) == ("01", "358.00", "20.00")

    # sobra só o resto da segunda parcela
    abertas = cliente.get(url, headers=davi).json()["parcelas"]
    assert [(p["id"], p["aberto"]) for p in abertas] == [(carnes["a_vencer"], "50.00")]
    # no caixa da loja que recebeu, cada forma; e não se estorna por lá
    sessao = cliente.get(f"/caixas/sessoes/{loja['sessao']}", headers=admin).json()
    lancamentos = [(x["descricao_motivo"], x["forma_pagamento"]["nome"], x["valor"]) for x in sessao["lancamentos"]]
    assert lancamentos == [("Recebimento de crediário", "Dinheiro", "100.00"),
                           ("Recebimento de crediário", "Cartão de crédito", "258.00")]
    lancamento = sessao["lancamentos"][0]["id"]
    assert cliente.post(f"/caixas/sessoes/{loja['sessao']}/lancamentos/{lancamento}/estornar", headers=admin).status_code == 422

    # recebeu errado: estorna, e as parcelas voltam a dever
    r = cliente.post(f"/crediario/recebimentos/{recebimento['id']}/estornar", headers=davi)
    assert r.status_code == 200 and r.json()["estornado_por"]["nome"] == "Davi Sem Acesso"
    assert [p["aberto"] for p in cliente.get(url, headers=davi).json()["parcelas"]] == ["300.00", "100.00"]
    sessao = cliente.get(f"/caixas/sessoes/{loja['sessao']}", headers=admin).json()
    assert all(x["estornado_em"] for x in sessao["lancamentos"])
    assert cliente.post(f"/crediario/recebimentos/{recebimento['id']}/estornar", headers=davi).status_code == 422


def test_juros_sugeridos():
    hoje = date(2026, 11, 2)
    assert contas.juros_sugerido(Decimal("100.00"), date(2026, 10, 2), Decimal("5"), hoje) == (31, Decimal("5.17"))
    assert contas.juros_sugerido(Decimal("100.00"), hoje, Decimal("5"), hoje) == (0, Decimal("0.00"))
