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


def test_consulta_das_contas_a_receber_com_filtros(cliente, cenario, loja, admin, carnes):  # noqa: F811
    r = cliente.get("/receber/parcelas", headers=admin).json()
    assert (r["total"], r["soma_aberto"], r["juros_ao_mes"]) == (2, "400.00", "5.00")
    vencida = r["itens"][0]  # do vencimento mais antigo para o mais novo
    assert (vencida["loja"]["codigo"], vencida["cliente"]["nome"], vencida["dias_atraso"], vencida["juros"]) == (
        "02", "Freguesa Ficticia", 20, "10.00")

    def total(**filtros):
        return cliente.get("/receber/parcelas", headers=admin, params=filtros).json()["total"]

    assert total(loja=cenario["e1"]) == 0 and total(loja=cenario["e2"]) == 2
    assert total(busca="fregues") == 2 and total(busca="ninguem") == 0
    assert total(ate=date.today().isoformat()) == 1  # só a vencida
    assert total(data="emissao", de=date.today().isoformat()) == 2
    assert total(valor="100.00") == 1 and total(origem="acerto") == 0
    assert cliente.get("/receber/parcelas", headers=admin, params={"ordem": "valor"}).json()["itens"][0]["aberto"] == "300.00"
    # a consulta pede a permissão própria
    assert cliente.get("/receber/parcelas", headers=loja["davi"]).status_code == 403


def test_prejuizo_tira_da_lista_mas_o_cliente_continua_devendo(cliente, loja, admin, carnes):  # noqa: F811
    vencida = carnes["vencida"]
    assert cliente.post("/receber/prejuizo", headers=admin, json={"parcelas": [vencida]}).status_code == 422  # sem motivo
    assert cliente.post("/receber/prejuizo", headers=loja["davi"],
                        json={"parcelas": [vencida], "motivo": "x"}).status_code == 403  # pede receber.prejuizo
    r = cliente.post("/receber/prejuizo", headers=admin, json={"parcelas": [vencida], "motivo": "Cliente não encontrado"})
    assert r.json() == {"alteradas": 1}

    def consulta(**filtros):
        return cliente.get("/receber/parcelas", headers=admin, params=filtros).json()

    assert (consulta()["total"], consulta()["soma_aberto"]) == (1, "100.00")  # saiu da lista
    so = consulta(prejuizo="so")["itens"]
    assert [(p["id"], p["prejuizo_motivo"], p["prejuizo_por"]) for p in so] == [(vencida, "Cliente não encontrado", "Caio Admin")]
    assert consulta(prejuizo="junto")["total"] == 2
    # continua devendo: aparece no recebimento, marcada, e conta no limite
    abertas = cliente.get(f"/crediario/clientes/{carnes['cliente']}/parcelas", headers=loja["davi"]).json()["parcelas"]
    assert [p["prejuizo"] for p in abertas] == [True, False]

    assert cliente.post("/receber/prejuizo/tirar", headers=admin, json={"parcelas": [vencida]}).json() == {"alteradas": 1}
    assert consulta()["total"] == 2


def test_contas_de_cobranca_mudanca_em_lote_e_volta_para_a_geral(cliente, loja, admin, carnes):  # noqa: F811
    contas = cliente.get("/receber/contas-cobranca", headers=admin).json()
    assert [(c["nome"], c["padrao"]) for c in contas] == [("Geral", True)]
    jose = cliente.post("/receber/contas-cobranca", headers=admin, json={"nome": "José Cobrador"}).json()
    assert cliente.post("/receber/contas-cobranca", headers=admin, json={"nome": "josé cobrador"}).status_code == 422
    geral = contas[0]["id"]
    assert cliente.put(f"/receber/contas-cobranca/{geral}", headers=admin, json={"nome": "Geral", "ativo": False}).status_code == 422

    # as duas parcelas vão para o cobrador, de uma vez
    parcelas = [carnes["vencida"], carnes["a_vencer"]]
    assert cliente.post("/receber/cobranca", headers=loja["davi"],
                        json={"parcelas": parcelas, "conta_cobranca_id": jose["id"]}).status_code == 403  # receber.cobranca
    r = cliente.post("/receber/cobranca", headers=admin, json={"parcelas": parcelas, "conta_cobranca_id": jose["id"]})
    assert r.json() == {"alteradas": 2}
    lista = cliente.get("/receber/parcelas", headers=admin, params={"conta_cobranca_id": jose["id"]}).json()
    assert [p["conta_cobranca"] for p in lista["itens"]] == ["José Cobrador", "José Cobrador"]

    # o cliente pagou tudo; os carnês voltam para a Geral e o recebimento avisa que quitou
    f = loja["formas"]
    r = cliente.post("/crediario/recebimentos", headers=loja["davi"], json={
        "sessao_caixa_id": loja["sessao"], "cliente_id": carnes["cliente"], "voltar_para_geral": True,
        "itens": [{"parcela_id": carnes["vencida"], "valor": "300.00"}, {"parcela_id": carnes["a_vencer"], "valor": "100.00"}],
        "pagamentos": [{"forma_pagamento_id": f["dinheiro"], "valor": "400.00"}],
    })
    assert r.status_code == 201, r.text
    assert r.json()["quitou"] is True
    todas = cliente.get("/receber/parcelas", headers=admin, params={"situacao": "todas"}).json()["itens"]
    assert {p["conta_cobranca"] for p in todas} == {"Geral"}


def test_prorrogar_em_lote_editar_e_historico(cliente, loja, admin, carnes):  # noqa: F811
    vencida, a_vencer = carnes["vencida"], carnes["a_vencer"]
    hoje = date.today()
    assert cliente.post("/receber/prorrogar", headers=loja["davi"], json={"parcelas": [vencida], "dias": 5}).status_code == 403
    r = cliente.post("/receber/prorrogar", headers=admin, json={"parcelas": [vencida], "dias": 5, "vencimento": "2030-01-01"})
    assert r.status_code == 422  # ou uma data, ou dias
    # as duas para o dia 30, com o que o cliente disse
    dia30 = date(hoje.year + 1, 1, 30)
    r = cliente.post("/receber/prorrogar", headers=admin,
                     json={"parcelas": [vencida, a_vencer], "vencimento": dia30.isoformat(), "anotacao": "Paga quando receber"})
    assert r.json() == {"alteradas": 2}
    linhas = {p["id"]: p for p in cliente.get("/receber/parcelas", headers=admin).json()["itens"]}
    assert linhas[vencida]["vencimento"] == dia30.isoformat()
    assert linhas[vencida]["vencimento_inicial"] == (hoje - timedelta(days=20)).isoformat()  # o inicial fica
    assert linhas[vencida]["dias_atraso"] == 0
    # mais 10 dias, cada uma a partir do seu vencimento
    cliente.post("/receber/prorrogar", headers=admin, json={"parcelas": [vencida], "dias": 10})

    # tipo e conta de cobrança da parcela; o que falta pagar não muda aqui
    jose = cliente.post("/receber/contas-cobranca", headers=admin, json={"nome": "José Cobrador"}).json()
    r = cliente.put(f"/receber/parcelas/{vencida}", headers=admin,
                    json={"tipo_cobranca": "boleto", "conta_cobranca_id": jose["id"], "aberto": "1.00"})
    assert r.status_code == 200
    linha = cliente.get("/receber/parcelas", headers=admin, params={"tipo_cobranca": "boleto"}).json()["itens"][0]
    assert (linha["conta_cobranca"], linha["aberto"]) == ("José Cobrador", "300.00")
    # o cabeçalho do documento
    r = cliente.put(f"/receber/documentos/{linha['conta_id']}", headers=admin, json={"historico": "Renegociada", "documento": "0009"})
    assert r.status_code == 200

    historico = cliente.get(f"/receber/parcelas/{vencida}/historico", headers=admin).json()
    assert [h["mudanca"] for h in historico] == ["documento", "cobranca", "tipo", "prorrogacao", "prorrogacao"]
    primeira, segunda = historico[4], historico[3]  # do mais novo para o mais antigo
    assert (primeira["de"], primeira["para"], primeira["anotacao"], primeira["usuario"]["nome"]) == (
        (hoje - timedelta(days=20)).strftime("%d/%m/%Y"), dia30.strftime("%d/%m/%Y"), "Paga quando receber", "Caio Admin")
    assert segunda["para"] == (dia30 + timedelta(days=10)).strftime("%d/%m/%Y")


def test_bloquear_e_liberar_clientes_em_lote(banco, cliente, loja, admin, carnes):  # noqa: F811
    r = cliente.post("/receber/clientes/bloqueio", headers=admin, json={"clientes": [carnes["cliente"]], "bloquear": True})
    assert r.json() == {"alterados": 1}
    assert cliente.get("/receber/parcelas", headers=admin, params={"bloqueio": "bloqueados"}).json()["total"] == 2
    with banco() as db:
        cli = db.get(Cliente, carnes["cliente"])
        assert cli.bloqueado and cli.anotacoes[0].texto == "Bloqueado pela cobrança (contas a receber)"
    r = cliente.post("/receber/clientes/bloqueio", headers=admin, json={"clientes": [carnes["cliente"]], "bloquear": False})
    assert r.json() == {"alterados": 1}


def test_busca_por_cliente_documento_ou_parcela(banco, cliente, cenario, loja, carnes):  # noqa: F811
    from app.nucleo.legado import MapaLegado
    from app.dominios.receber.modelos import ParcelaReceber
    davi = loja["davi"]
    with banco() as db:
        vencida = db.get(ParcelaReceber, carnes["vencida"])
        vencida.conta.documento_legado = "0000777"  # veio do VB6, com o "Nº Seq." 0001234
        db.add(MapaLegado(tabela="tab_itdoc", empresa_id=cenario["e2"], codigo="0001234", novo_id=vencida.id))
        conta_nova = db.get(ParcelaReceber, carnes["a_vencer"]).conta_id
        db.commit()

    def busca(termo):
        return cliente.get("/crediario/busca", headers=davi, params={"termo": termo}).json()

    assert [(a["como"], a["cliente"]["nome"]) for a in busca("fregues")] == [("cliente", "Freguesa Ficticia")]
    assert [(a["como"], a["documento"]) for a in busca("777")] == [("documento", "02-0000777")]  # sem os zeros
    achado = busca("1234")[0]
    assert (achado["como"], achado["parcela_id"]) == ("parcela", carnes["vencida"])
    assert achado["parcela"].startswith("1/1, vence")
    # o carnê novo: pelo número do carnê e pelo número da parcela
    assert ("documento", conta_nova) in [(a["como"], a["conta_id"]) for a in busca(str(conta_nova))]
    assert [a["parcela_id"] for a in busca(str(carnes["a_vencer"])) if a["como"] == "parcela"] == [carnes["a_vencer"]]
    assert busca("ninguem") == []
