"""Venda: o vendedor monta, o caixa recebe (D26). Dados fictícios."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.acesso.modelos import Perfil
from app.dominios.cidades.modelos import Cidade
from app.dominios.empresas.modelos import Empresa
from app.dominios.estoque.modelos import Estoque
from app.dominios.produtos.modelos import Produto
from app.dominios.vendas.modelos import Venda


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    return _auth(cliente, "caio", cenario["e1"])


@pytest.fixture
def loja(banco, cliente, cenario, admin):
    """Formas, dois produtos, um caixa aberto, o vendedor davi (até 2% de desconto) e a gerente ana (até 15%)."""
    formas = {}
    for dados in [
        {"nome": "Dinheiro", "tipo": "dinheiro", "desconto": "5"},
        {"nome": "Cartão de crédito", "tipo": "cartao_credito", "parcelas": 10, "parcelas_sem_autorizacao": 3},
        {"nome": "Crediário", "tipo": "crediario", "parcelas": 10, "parcelas_sem_autorizacao": 6},
    ]:
        formas[dados["tipo"]] = cliente.post("/formas-pagamento", headers=admin, json=dados).json()["id"]
    with banco() as db:
        lencol = Produto(codigo=1, nome="Lençol Ficticio Casal", preco_venda=Decimal("100.00"))
        toalha = Produto(codigo=2, nome="Toalha Ficticia", preco_venda=Decimal("30.00"), preco_queima=Decimal("20.00"))
        tecido = Produto(codigo=3, nome="Tecido Ficticio", unidade="M", fracionado=True, preco_venda=Decimal("10.00"))
        lencol2 = Produto(codigo=4, nome="Lençol Ficticio Solteiro", preco_venda=Decimal("50.00"))
        db.add_all([lencol, toalha, tecido, lencol2])
        db.flush()
        db.add(Estoque(empresa_id=cenario["e1"], produto_id=lencol.id, quantidade=Decimal("5"), reservado=Decimal(0)))
        vendedor = acesso.criar_perfil(db, "Vendedor", ["vendas.vender", "caixa.operar"])
        vendedor.desconto_maximo = Decimal("2")
        gerente = db.get(Perfil, repositorio.acesso(db, repositorio.usuario_por_login(db, "ana").id, cenario["e1"]).perfil_id)
        gerente.desconto_maximo = Decimal("15")
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "davi"), db.get(Empresa, cenario["e1"]), vendedor)
        db.commit()
        produtos = {"lencol": lencol.id, "toalha": toalha.id, "tecido": tecido.id, "lencol2": lencol2.id}
    caixa = cliente.post("/caixas", headers=admin, json={"nome": "Cx 02"}).json()
    sessao = cliente.post(f"/caixas/{caixa['id']}/abrir", headers=admin, json={"fundo": "50"}).json()
    return {"formas": formas, "produtos": produtos, "sessao": sessao["id"], "davi": _auth(cliente, "davi", cenario["e1"])}


def test_monta_a_venda_e_o_caixa_recebe(banco, cliente, cenario, admin, loja):
    davi, p = loja["davi"], loja["produtos"]
    venda = cliente.post("/vendas", headers=davi).json()
    assert (venda["situacao"], venda["vendedor"]["nome"], venda["total"]) == ("aberta", "Davi Sem Acesso", "0.00")
    url = f"/vendas/{venda['id']}"

    r = cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["lencol"], "quantidade": "2"})
    assert r.status_code == 200, r.text
    cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["lencol"]})  # o mesmo produto soma na linha
    venda = cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["toalha"]}).json()
    assert [(i["descricao"], i["quantidade"], i["preco"]) for i in venda["itens"]] == [
        ("Lençol Ficticio Casal", "3.000", "100.00"),
        ("Toalha Ficticia", "1.000", "20.00"),  # com preço de queima, sai por ele
    ]
    assert [i["disponivel"] for i in venda["itens"]] == ["5.000", "0.000"]
    assert cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["toalha"], "quantidade": "0.5"}).status_code == 422
    assert cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["tecido"], "quantidade": "1.5"}).status_code == 200

    # no dinheiro, os 5% da forma vão para os itens, sem pedir autorização; a toalha está em queima e fica sem desconto
    dados = {"forma_pagamento_id": loja["formas"]["dinheiro"]}
    venda = cliente.put(url, headers=davi, json=dados).json()
    assert (venda["subtotal"], venda["desconto"], venda["total"]) == ("335.00", "15.75", "319.25")
    assert [(i["desconto"], i["em_queima"]) for i in venda["itens"]] == [("15.00", False), ("0.00", True), ("0.75", False)]
    assert sum(Decimal(i["total"]) for i in venda["itens"]) == Decimal(venda["total"])

    # o caixa só recebe depois que o vendedor fecha, e para fechar é preciso o nome de quem compra
    r = cliente.post(f"{url}/receber", headers=davi, json={"sessao_caixa_id": loja["sessao"]})
    assert r.status_code == 422 and r.json()["detail"] == "O vendedor ainda não fechou esta venda"
    r = cliente.post(f"{url}/fechar", headers=davi)
    assert r.status_code == 422 and r.json()["detail"] == "Informe o nome de quem está comprando"
    venda = cliente.put(url, headers=davi, json=dados | {"consumidor": {"nome": "José"}}).json()
    assert (venda["comprador"], venda["consumidor"]) == ("José", None)  # só com o nome, não vira cadastro
    venda = cliente.post(f"{url}/fechar", headers=davi).json()
    assert venda["situacao"] == "fechada" and venda["fechada_em"]
    r = cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["lencol"]})
    assert r.status_code == 422 and "reabra" in r.json()["detail"]
    assert cliente.get("/vendas", headers=davi, params={"situacao": "fechada", "busca": "jos"}).json()["total"] == 1

    # o caixa recebe: entra no caixa e baixa o estoque
    no_dinheiro = {"sessao_caixa_id": loja["sessao"], "valor_recebido": "320",
                   "pagamentos": [{"forma_pagamento_id": loja["formas"]["dinheiro"], "valor": "319.25"}]}
    r = cliente.post(f"{url}/receber", headers=davi, json=no_dinheiro)
    assert r.status_code == 200, r.text
    venda = r.json()
    assert (venda["situacao"], venda["troco"], venda["recebida_por"]["nome"]) == ("recebida", "0.75", "Davi Sem Acesso")
    assert venda["avisos"] == ["Toalha Ficticia: o estoque da loja ficou em -1", "Tecido Ficticio: o estoque da loja ficou em -1.5"]
    sessao = cliente.get(f"/caixas/sessoes/{loja['sessao']}", headers=admin).json()
    assert [(x["descricao_motivo"], x["valor"], x["documento"]) for x in sessao["lancamentos"]] == [("Venda", "319.25", f"venda {venda['numero']}")]
    assert sessao["totais"][0]["saldo"] == "369.25"  # fundo 50 + venda
    lancamento = sessao["lancamentos"][0]["id"]
    assert cliente.post(f"/caixas/sessoes/{loja['sessao']}/lancamentos/{lancamento}/estornar", headers=admin).status_code == 422
    with banco() as db:
        assert db.query(Estoque).filter_by(empresa_id=cenario["e1"], produto_id=p["lencol"]).one().quantidade == 2

    # recebida não muda mais
    assert cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["lencol"]}).status_code == 422
    assert cliente.post(f"{url}/receber", headers=davi, json={"sessao_caixa_id": loja["sessao"]}).status_code == 422


def test_desconto_no_total_e_rateado_e_acima_do_limite_pede_autorizacao(cliente, loja):
    davi, p = loja["davi"], loja["produtos"]
    url = f"/vendas/{cliente.post('/vendas', headers=davi).json()['id']}"
    cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["lencol"]})
    cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["tecido"], "quantidade": "3.3"})  # 33,00

    # 2% é o limite do davi
    venda = cliente.post(f"{url}/desconto", headers=davi, json={"valor": "2.66"}).json()
    assert [i["desconto"] for i in venda["itens"]] == ["2.00", "0.66"]
    r = cliente.post(f"{url}/desconto", headers=davi, json={"percentual": "10"})
    assert (r.status_code, r.headers.get("x-pede-autorizacao")) == (403, "sim")
    assert "passa do seu limite (2%)" in r.json()["detail"]
    assert cliente.get(url, headers=davi).json()["desconto"] == "2.66"  # nada mudou

    errada = cliente.post(f"{url}/desconto", headers=davi, json={"percentual": "10", "autorizacao": {"login": "ana", "senha": "x"}})
    assert errada.status_code == 422
    r = cliente.post(f"{url}/desconto", headers=davi, json={"percentual": "20", "autorizacao": {"login": "ana", "senha": "senha-ana"}})
    assert r.status_code == 403 and "limite de Ana Lima (15%)" in r.json()["detail"]
    venda = cliente.post(f"{url}/desconto", headers=davi, json={"percentual": "10", "autorizacao": {"login": "ana", "senha": "senha-ana"}}).json()
    assert (venda["desconto"], venda["desconto_autorizado_por"]["nome"]) == ("13.30", "Ana Lima")
    # com a autorização dada, o desconto no item vai até o limite de quem autorizou
    item = venda["itens"][0]
    venda = cliente.put(f"{url}/itens/{item['id']}", headers=davi, json={"quantidade": "1", "desconto": "15"}).json()
    assert (venda["itens"][0]["total"], venda["total"]) == ("85.00", "114.70")
    assert cliente.put(f"{url}/itens/{item['id']}", headers=davi, json={"quantidade": "1", "desconto": "30"}).status_code == 403
    # item novo leva o % da venda, menos o em queima
    venda = cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["lencol2"]}).json()
    assert venda["itens"][2]["desconto"] == "5.00"
    venda = cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["toalha"]}).json()
    toalha = venda["itens"][3]
    assert (toalha["desconto"], toalha["em_queima"]) == ("0.00", True)
    r = cliente.put(f"{url}/itens/{toalha['id']}", headers=davi, json={"quantidade": "1", "desconto": "1"})
    assert r.status_code == 422 and r.json()["detail"] == "Toalha Ficticia está em queima e não tem desconto"
    # o desconto no total é rateado só entre os que aceitam desconto
    venda = cliente.post(f"{url}/desconto", headers=davi, json={"valor": "10.00"}).json()
    assert [i["desconto"] for i in venda["itens"]] == ["5.47", "1.80", "2.73", "0.00"]


def test_parcelas_acima_do_limite_da_forma(cliente, loja, admin):
    davi = loja["davi"]
    url = f"/vendas/{cliente.post('/vendas', headers=davi).json()['id']}"
    cliente.post(f"{url}/itens", headers=davi, json={"produto_id": loja["produtos"]["lencol"]})
    cartao = loja["formas"]["cartao_credito"]
    assert cliente.put(url, headers=davi, json={"forma_pagamento_id": cartao, "parcelas": 3}).status_code == 200
    assert cliente.put(url, headers=davi, json={"forma_pagamento_id": cartao, "parcelas": 11}).status_code == 422
    r = cliente.put(url, headers=davi, json={"forma_pagamento_id": cartao, "parcelas": 5})
    assert r.status_code == 403 and "acima de 3x" in r.json()["detail"]
    # a ana é gerente, mas o perfil dela não tem vendas.autorizar
    r = cliente.put(url, headers=davi, json={"forma_pagamento_id": cartao, "parcelas": 5,
                                              "autorizacao": {"login": "ana", "senha": "senha-ana"}})
    assert r.status_code == 403 and "Ana Lima não pode" in r.json()["detail"]
    venda = cliente.put(url, headers=davi, json={"forma_pagamento_id": cartao, "parcelas": 5,
                                                 "autorizacao": {"login": "caio", "senha": "senha-caio"}}).json()
    assert (venda["parcelas"], venda["parcelas_autorizadas_por"]["nome"]) == (5, "Caio Admin")

    # o crediário pede o cliente cadastrado (o consumidor só com o nome não basta)
    cliente.put(url, headers=davi, json={"forma_pagamento_id": loja["formas"]["crediario"], "parcelas": 2,
                                         "consumidor": {"nome": "José"}})
    r = cliente.post(f"{url}/fechar", headers=davi)
    assert r.status_code == 422 and r.json()["detail"] == "O crediário pede o cliente cadastrado"


def test_lista_vence_e_cancela(banco, cliente, cenario, loja, admin):
    davi = loja["davi"]
    primeira = cliente.post("/vendas", headers=davi).json()
    segunda = cliente.post("/vendas", headers=admin).json()
    assert segunda["numero"] == primeira["numero"] + 1
    with banco() as db:  # a primeira foi aberta há 11 dias
        db.get(Venda, primeira["id"]).vence_em = datetime.now() - timedelta(days=1)
        db.commit()
    r = cliente.get("/vendas", headers=davi, params={"situacao": "aberta"}).json()
    assert [v["numero"] for v in r["itens"]] == [segunda["numero"]]
    assert cliente.get(f"/vendas/{primeira['id']}", headers=davi).json()["situacao"] == "vencida"
    assert [v["id"] for v in cliente.get("/vendas", headers=davi, params={"minhas": True}).json()["itens"]] == [primeira["id"]]
    assert cliente.post(f"/vendas/{primeira['id']}/receber", headers=davi, json={"sessao_caixa_id": loja["sessao"]}).status_code == 422

    venda = cliente.post(f"/vendas/{segunda['id']}/cancelar", headers=davi, json={"motivo": "Cliente desistiu"}).json()
    assert (venda["situacao"], venda["cancelada_por"]["nome"]) == ("cancelada", "Davi Sem Acesso")
    # de outra loja não vê
    bia = _auth(cliente, "bia", cenario["e2"])
    assert cliente.get(f"/vendas/{primeira['id']}", headers=bia).status_code == 403  # sem permissão de vendas na 02


def test_perfil_com_limite_de_desconto(cliente, cenario, admin):
    r = cliente.post("/acesso/perfis", headers=admin, json={"nome": "Caixa", "desconto_maximo": "5", "permissoes": []})
    assert (r.status_code, r.json()["desconto_maximo"]) == (201, "5.00")
    # a gerente ana não tem limite de desconto: não pode dar a outro perfil
    ana = _auth(cliente, "ana", cenario["e1"])
    r = cliente.put(f"/acesso/perfis/{r.json()['id']}", headers=ana, json={"nome": "Caixa", "desconto_maximo": "10", "permissoes": []})
    assert r.status_code == 403 and "desconto máximo" in r.json()["detail"]


def test_consumidor_sem_cadastro_e_entrega(banco, cliente, loja):
    davi, p = loja["davi"], loja["produtos"]
    url = f"/vendas/{cliente.post('/vendas', headers=davi).json()['id']}"
    cliente.post(f"{url}/itens", headers=davi, json={"produto_id": p["lencol"]})
    dinheiro = loja["formas"]["dinheiro"]

    # com o CPF (ou telefone, ou e-mail), vira o cadastro curto do consumidor
    maria = {"nome": "Maria", "cpf": "529.982.247-25", "dia_nascimento": 15, "mes_nascimento": 3,
             "telefone": "(62) 99999-0000", "email": "maria@exemplo.com"}
    assert cliente.put(url, headers=davi, json={"consumidor": maria | {"cpf": "111.111.111-11"}}).status_code == 422
    assert cliente.put(url, headers=davi, json={"consumidor": maria | {"mes_nascimento": None}}).status_code == 422
    venda = cliente.put(url, headers=davi, json={"forma_pagamento_id": dinheiro, "consumidor": maria}).json()
    assert venda["comprador"] == "Maria"
    assert {k: venda["consumidor"][k] for k in ("cpf", "telefone", "dia_nascimento")} == {
        "cpf": "52998224725", "telefone": "62999990000", "dia_nascimento": 15}
    # na próxima compra, o CPF traz o que já se sabe
    achado = cliente.get("/consumidores/52998224725", headers=davi).json()
    assert (achado["cliente"], achado["consumidor"]["email"]) == (None, "maria@exemplo.com")
    assert cliente.get("/consumidores/11111111111", headers=davi).status_code == 422

    # com entrega: a taxa entra no total, sem desconto, e o endereço é pedido para fechar
    entrega = {"taxa": "15.00", "logradouro": "Rua Ficticia", "numero": "10", "bairro": "Centro"}
    venda = cliente.put(url, headers=davi, json={"forma_pagamento_id": dinheiro, "consumidor": maria,
                                                 "entrega": entrega}).json()
    assert (venda["desconto"], venda["taxa_entrega"], venda["total"]) == ("5.00", "15.00", "110.00")
    r = cliente.post(f"{url}/fechar", headers=davi)
    assert r.status_code == 422 and r.json()["detail"] == "Falta o endereço da entrega: rua, número, bairro e cidade"
    with banco() as db:
        cidade = Cidade(codigo_ibge="5208707", nome="Goiânia", uf="GO", nome_busca="goiania")
        db.add(cidade)
        db.commit()
        cidade_id = cidade.id
    venda = cliente.put(url, headers=davi, json={"forma_pagamento_id": dinheiro, "consumidor": maria,
                                                 "entrega": entrega | {"cidade_id": cidade_id}}).json()
    assert venda["entrega"]["cidade"]["nome"] == "Goiânia"
    assert cliente.post(f"{url}/fechar", headers=davi).json()["situacao"] == "fechada"

    # o caixa devolve para o vendedor, que tira a entrega e fecha de novo
    assert cliente.post(f"{url}/reabrir", headers=davi).json()["situacao"] == "aberta"
    venda = cliente.put(url, headers=davi, json={"forma_pagamento_id": dinheiro, "consumidor": maria}).json()
    assert (venda["entrega"], venda["total"]) == (None, "95.00")
    assert cliente.post(f"{url}/fechar", headers=davi).json()["situacao"] == "fechada"
    r = cliente.post(f"{url}/receber", headers=davi, json={
        "sessao_caixa_id": loja["sessao"], "pagamentos": [{"forma_pagamento_id": dinheiro, "valor": "95.00"}]})
    assert r.status_code == 200, r.text


def test_no_caixa_muda_a_forma_e_paga_em_varias(cliente, loja):
    davi, f = loja["davi"], loja["formas"]
    url = f"/vendas/{cliente.post('/vendas', headers=davi).json()['id']}"
    cliente.post(f"{url}/itens", headers=davi, json={"produto_id": loja["produtos"]["lencol"]})
    cliente.put(url, headers=davi, json={"forma_pagamento_id": f["dinheiro"], "consumidor": {"nome": "José"}})
    assert cliente.post(f"{url}/fechar", headers=davi).json()["total"] == "95.00"

    # no caixa, o cliente prefere o cartão: o desconto da forma é outro (0%), e o da venda cai
    venda = cliente.post(f"{url}/forma", headers=davi, json={"forma_pagamento_id": f["cartao_credito"]}).json()
    assert (venda["situacao"], venda["forma_pagamento"]["nome"], venda["total"]) == ("fechada", "Cartão de crédito", "100.00")
    # um pouco no dinheiro, um pouco no cartão
    pedido = {"sessao_caixa_id": loja["sessao"], "valor_recebido": "50", "pagamentos": [
        {"forma_pagamento_id": f["dinheiro"], "valor": "40.00"}, {"forma_pagamento_id": f["cartao_credito"], "valor": "50.00"}]}
    r = cliente.post(f"{url}/receber", headers=davi, json=pedido)
    assert r.status_code == 422 and r.json()["detail"] == "Falta lançar R$ 10,00"
    pedido["pagamentos"][1] |= {"valor": "60.00", "parcelas": 5}
    r = cliente.post(f"{url}/receber", headers=davi, json=pedido)
    assert r.status_code == 403 and "acima de 3x" in r.json()["detail"]
    pedido["pagamentos"][1]["parcelas"] = 3
    r = cliente.post(f"{url}/receber", headers=davi, json=pedido | {"modelo_nota": "55"})
    assert r.status_code == 422 and "NF-e (modelo 55)" in r.json()["detail"]
    venda = cliente.post(f"{url}/receber", headers=davi, json=pedido).json()
    assert (venda["situacao"], venda["troco"], venda["modelo_nota"]) == ("recebida", "10.00", "65")
    assert [(p["forma_pagamento"]["nome"], p["valor"], p["parcelas"]) for p in venda["pagamentos"]] == [
        ("Dinheiro", "40.00", 1), ("Cartão de crédito", "60.00", 3)]


def _venda_recebida(cliente, loja, quem, quantidade="2"):
    url = f"/vendas/{cliente.post('/vendas', headers=quem).json()['id']}"
    cliente.post(f"{url}/itens", headers=quem, json={"produto_id": loja["produtos"]["lencol"], "quantidade": quantidade})
    dinheiro = loja["formas"]["dinheiro"]
    cliente.put(url, headers=quem, json={"forma_pagamento_id": dinheiro, "consumidor": {"nome": "José"}})
    cliente.post(f"{url}/fechar", headers=quem)
    total = cliente.get(url, headers=quem).json()["total"]
    r = cliente.post(f"{url}/receber", headers=quem, json={
        "sessao_caixa_id": loja["sessao"], "pagamentos": [{"forma_pagamento_id": dinheiro, "valor": total}]})
    assert r.status_code == 200, r.text
    return url


def test_cancelar_venda_recebida(banco, cliente, cenario, loja, admin):
    url = _venda_recebida(cliente, loja, admin)
    with banco() as db:
        assert db.query(Estoque).filter_by(empresa_id=cenario["e1"], produto_id=loja["produtos"]["lencol"]).one().quantidade == 3
    # o davi vende e recebe, mas não cancela a recebida
    r = cliente.post(f"{url}/cancelar", headers=loja["davi"], json={"motivo": "Cliente desistiu"})
    assert r.status_code == 403 and "vendas.cancelar" in r.json()["detail"]

    # com o caixa do recebimento aberto: os lançamentos são estornados, o estoque volta
    venda = cliente.post(f"{url}/cancelar", headers=admin, json={"motivo": "Cliente desistiu"}).json()
    assert (venda["situacao"], venda["motivo_cancelamento"]) == ("cancelada", "Cliente desistiu")
    sessao = cliente.get(f"/caixas/sessoes/{loja['sessao']}", headers=admin).json()
    assert all(x["estornado_em"] for x in sessao["lancamentos"])
    with banco() as db:
        assert db.query(Estoque).filter_by(empresa_id=cenario["e1"], produto_id=loja["produtos"]["lencol"]).one().quantidade == 5

    # prazo curto: recebida há mais de 7 dias, não cancela
    url = _venda_recebida(cliente, loja, admin, "1")
    with banco() as db:
        db.get(Venda, int(url.rsplit("/", 1)[1])).recebida_em = datetime.now() - timedelta(days=8)
        db.commit()
    r = cliente.post(f"{url}/cancelar", headers=admin, json={"motivo": "Atrasado"})
    assert r.status_code == 422 and "mais de 7 dias" in r.json()["detail"]


def test_cancelar_com_o_caixa_do_recebimento_ja_fechado(banco, cliente, cenario, loja, admin):
    from app.dominios.caixa.modelos import FECHADO, SessaoCaixa
    url = _venda_recebida(cliente, loja, admin, "1")
    with banco() as db:
        db.get(SessaoCaixa, loja["sessao"]).situacao = FECHADO
        db.commit()
    caixa = cliente.post("/caixas", headers=admin, json={"nome": "Cx 03"}).json()
    nova = cliente.post(f"/caixas/{caixa['id']}/abrir", headers=admin, json={"fundo": "100"}).json()
    r = cliente.post(f"{url}/cancelar", headers=admin, json={"motivo": "Defeito"})
    assert r.status_code == 422 and "já foi fechado" in r.json()["detail"]
    r = cliente.post(f"{url}/cancelar", headers=admin, json={"motivo": "Defeito", "sessao_caixa_id": nova["id"]})
    assert r.status_code == 200, r.text
    saidas = cliente.get(f"/caixas/sessoes/{nova['id']}", headers=admin).json()["lancamentos"]
    assert [(x["tipo"], x["descricao_motivo"], x["valor"]) for x in saidas] == [("saida", "Cancelamento de venda", "95.00")]
