"""Acerto do consignado (D30): para o cliente do representante (carnê no nome dele, comissão pelas parcelas) ou para
o próprio representante (a comissão vira desconto), a prazo ou à vista, e o de queima. Dados fictícios."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.clientes.modelos import Cliente
from app.dominios.consignacao.modelos import ComissaoParcela, Representante
from app.dominios.empresas.modelos import Empresa
from app.dominios.estoque.modelos import Estoque, MovimentoEstoque
from app.dominios.produtos.modelos import Produto
from app.dominios.receber import servico as contas
from app.dominios.receber.modelos import ContaReceber
from app.nucleo.seguranca import gerar_hash
from tests.test_transferencias import _auth, _transferir


@pytest.fixture
def consignado(banco, cliente, cenario):
    """O representante 7 com um perfume (R$ 120) e duas toalhas (R$ 30, em queima por R$ 20), a freguesa dele (limite
    R$ 1.000), as formas, o caixa do consignado aberto e o davi no balcão e no acerto."""
    admin = _auth(cliente, "caio", cenario["e1"])
    formas = {}
    for dados in [
        {"nome": "Dinheiro", "tipo": "dinheiro"},
        {"nome": "Cartão de crédito", "tipo": "cartao_credito", "parcelas": 10, "parcelas_sem_autorizacao": 3},
        {"nome": "Crediário", "tipo": "crediario", "parcelas": 10, "parcelas_sem_autorizacao": 6},
    ]:
        formas[dados["tipo"]] = cliente.post("/formas-pagamento", headers=admin, json=dados).json()["id"]
    with banco() as db:
        maria = Cliente(nome="Maria Ficticia", cpf_cnpj="52998224725", limite_credito=Decimal("1000.00"))
        freguesa = Cliente(nome="Freguesa Ficticia", cpf_cnpj="00000000191", limite_credito=Decimal("1000.00"))
        db.add_all([maria, freguesa])
        db.flush()
        rep = Representante(codigo=7, cliente_id=maria.id, limite=Decimal("1000.00"),
                            senha_hash=gerar_hash("gato", sem_caixa=True), lembrete_acerto="Cobrar a sacola")
        perfume = Produto(codigo=1, nome="Perfume Ficticio", preco_venda=Decimal("120.00"))
        toalha = Produto(codigo=2, nome="Toalha Ficticia", preco_venda=Decimal("30.00"), preco_queima=Decimal("20.00"))
        db.add_all([rep, perfume, toalha])
        db.flush()
        for produto in (perfume, toalha):
            db.add(Estoque(empresa_id=cenario["e1"], produto_id=produto.id, quantidade=Decimal("5"), reservado=Decimal(0)))
        perfil = acesso.criar_perfil(db, "Consignado", ["consignacao.transferir", "consignacao.acertar"])
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "davi"), db.get(Empresa, cenario["e1"]), perfil)
        db.commit()
        ids = {"rep": rep.id, "maria": maria.id, "freguesa": freguesa.id, "perfume": perfume.id, "toalha": toalha.id}
    caixa = cliente.post("/caixas", headers=admin, json={"nome": "Consignado"}).json()
    sessao = cliente.post(f"/caixas/{caixa['id']}/abrir", headers=admin, json={"fundo": "0"}).json()
    davi = _auth(cliente, "davi", cenario["e1"])
    _transferir(cliente, davi, ids["rep"], ids["perfume"], "2")
    _transferir(cliente, davi, ids["rep"], ids["toalha"], "2")
    com_ele = {i["descricao"]: i["id"] for i in cliente.get(f"/representantes/{ids['rep']}/com-ele", headers=davi).json()}
    return ids | {"davi": davi, "admin": admin, "formas": formas, "sessao": sessao["id"], "com_ele": com_ele}


def _abrir(cliente, c):
    a = cliente.post("/consignacao/acertos", headers=c["davi"], json={"representante_id": c["rep"]}).json()
    return a, f"/consignacao/acertos/{a['id']}"


def test_acerto_para_o_cliente_a_prazo(banco, cliente, cenario, consignado):
    c, davi = consignado, consignado["davi"]
    a, url = _abrir(cliente, c)
    assert (a["numero"], a["situacao"], a["para"], a["representante"]["lembrete_acerto"]) == (1, "aberta", "cliente", "Cobrar a sacola")
    r = cliente.post(f"{url}/itens", headers=davi, json={"item_transferencia_id": c["com_ele"]["Perfume Ficticio"], "quantidade": "3"})
    assert r.status_code == 422 and "só restam 2" in r.json()["detail"]
    cliente.post(f"{url}/itens", headers=davi, json={"item_transferencia_id": c["com_ele"]["Perfume Ficticio"], "quantidade": "2"})

    # à vista é só para o próprio representante
    r = cliente.put(url, headers=davi, json={"para": "cliente", "cliente_id": c["freguesa"], "pagamento": "vista"})
    assert r.status_code == 422 and "só para o próprio representante" in r.json()["detail"]
    primeiro = date.today() + timedelta(days=30)
    # vendeu por 260: a diferença de 20 fica para ele; comissão = 15% (cobrança no cliente, a padrão) × 240 + 20
    a = cliente.put(url, headers=davi, json={"para": "cliente", "cliente_id": c["freguesa"], "tipo_comissao": "cliente",
                                             "negociado": "260.00", "parcelas": 3,
                                             "primeiro_vencimento": primeiro.isoformat()}).json()
    assert (a["total_inicial"], a["diferenca"], a["percentual"], a["comissao"], a["valor"]) == (
        "240.00", "20.00", "15.00", "56.00", "260.00")
    assert (a["cliente"]["nome"], a["nome_comissao"]) == ("Freguesa Ficticia", "Cobrança no cliente")

    entrada = [{"forma_pagamento_id": c["formas"]["dinheiro"], "valor": "20.00"}]
    r = cliente.post(f"{url}/confirmar", headers=davi, json={"sessao_caixa_id": c["sessao"], "pagamentos": entrada})
    assert r.status_code == 200, r.text
    a = r.json()
    assert (a["situacao"], a["entrada"], a["a_prazo"]) == ("confirmada", "20.00", "240.00")
    # o carnê, no nome da freguesa, com a comissão dividida pelas parcelas
    assert [(p["numero"], p["vencimento"], p["valor"], p["comissao"]) for p in a["carne"]] == [
        (1, primeiro.isoformat(), "80.00", "18.66"),
        (2, contas.somar_meses(primeiro, 1).isoformat(), "80.00", "18.66"),
        (3, contas.somar_meses(primeiro, 2).isoformat(), "80.00", "18.68")]
    with banco() as db:
        conta = db.get(ContaReceber, a["conta_id"])
        assert (conta.cliente_id, conta.origem, conta.documento, conta.parcelas[0].tipo_cobranca) == (
            c["freguesa"], "acerto", "01-acerto 1", "cliente")
        assert db.query(ComissaoParcela).filter_by(representante_id=c["rep"]).count() == 3
        perfume = db.query(Estoque).filter_by(empresa_id=cenario["e1"], produto_id=c["perfume"]).one()
        assert (perfume.quantidade, perfume.reservado) == (3, 0)  # saiu da loja e do que estava com ele
        mov = db.query(MovimentoEstoque).filter_by(tipo="consignacao_acerto").one()
        assert (mov.quantidade, mov.reservado, mov.documento) == (-2, -2, "acerto 1")
    sessao = cliente.get(f"/caixas/sessoes/{c['sessao']}", headers=c["admin"]).json()
    assert sorted((x["forma_pagamento"]["nome"], x["valor"], x["documento"]) for x in sessao["lancamentos"]) == [
        ("Crediário", "240.00", "acerto 1"), ("Dinheiro", "20.00", "acerto 1")]
    assert [i["descricao"] for i in cliente.get(f"/representantes/{c['rep']}/com-ele", headers=davi).json()] == ["Toalha Ficticia"]
    carne = cliente.get(f"{url}/carne", headers=davi).json()
    assert (carne["documento"], carne["venda"], carne["cliente"]["nome"], carne["carne"]["valor"]) == (
        "acerto 1", None, "Freguesa Ficticia", "240.00")
    assert cliente.put(url, headers=davi, json={"para": "cliente"}).status_code == 422  # confirmado não muda


def test_acerto_passa_do_limite_pede_a_gerencia(banco, cliente, consignado):
    c, davi = consignado, consignado["davi"]
    with banco() as db:
        db.get(Cliente, c["freguesa"]).limite_credito = Decimal("100.00")
        db.commit()
    a, url = _abrir(cliente, c)
    cliente.post(f"{url}/itens", headers=davi, json={"item_transferencia_id": c["com_ele"]["Perfume Ficticio"]})
    cliente.put(url, headers=davi, json={"para": "cliente", "cliente_id": c["freguesa"], "parcelas": 2,
                                         "primeiro_vencimento": (date.today() + timedelta(days=30)).isoformat()})
    pedido = {"sessao_caixa_id": c["sessao"]}
    r = cliente.post(f"{url}/confirmar", headers=davi, json=pedido)
    assert r.status_code == 403 and r.headers["x-pede-autorizacao"] == "sim"
    assert "passa do limite disponível de Freguesa Ficticia (R$ 100,00)" in r.json()["detail"]
    r = cliente.post(f"{url}/confirmar", headers=davi, json=pedido | {"autorizacao": {"login": "caio", "senha": "senha-caio"}})
    assert r.status_code == 200, r.text
    assert (r.json()["autorizada_por"]["nome"], r.json()["a_prazo"]) == ("Caio Admin", "120.00")
    with banco() as db:
        db.get(Cliente, c["freguesa"]).bloqueado = True
        db.commit()
    a, url = _abrir(cliente, c)
    cliente.post(f"{url}/itens", headers=davi, json={"item_transferencia_id": c["com_ele"]["Perfume Ficticio"]})
    cliente.put(url, headers=davi, json={"para": "cliente", "cliente_id": c["freguesa"],
                                         "primeiro_vencimento": date.today().isoformat()})
    r = cliente.post(f"{url}/confirmar", headers=davi, json=pedido)
    assert r.status_code == 422 and "bloqueado e não pode receber o acerto a prazo" in r.json()["detail"]


def test_acerto_para_o_representante(banco, cliente, consignado):
    c, davi = consignado, consignado["davi"]
    a, url = _abrir(cliente, c)
    cliente.post(f"{url}/itens", headers=davi, json={"item_transferencia_id": c["com_ele"]["Toalha Ficticia"], "quantidade": "2"})
    # à vista no dinheiro: 25% de desconto; a diferença não muda nada para ele
    a = cliente.put(url, headers=davi, json={"para": "representante", "pagamento": "vista", "negociado": "70.00"}).json()
    assert (a["cliente"]["nome"], a["tipo_comissao"], a["percentual"], a["comissao"], a["valor"]) == (
        "Maria Ficticia", "vista_dinheiro", "25.00", "25.00", "45.00")
    pedido = {"sessao_caixa_id": c["sessao"]}
    r = cliente.post(f"{url}/confirmar", headers=davi, json=pedido | {"pagamentos": [
        {"forma_pagamento_id": c["formas"]["cartao_credito"], "valor": "45.00"}]})
    assert r.status_code == 422 and "não pode ser pago em Cartão de crédito" in r.json()["detail"]
    # no cartão parcelado, 15%
    a = cliente.put(url, headers=davi, json={"para": "representante", "pagamento": "vista", "tipo_comissao": "vista_parcelado",
                                             "negociado": "70.00"}).json()
    assert (a["percentual"], a["valor"]) == ("15.00", "51.00")
    r = cliente.post(f"{url}/confirmar", headers=davi, json=pedido | {"pagamentos": [
        {"forma_pagamento_id": c["formas"]["cartao_credito"], "valor": "50.00", "parcelas": 2}]})
    assert r.status_code == 422 and "tem que ser o valor do acerto, R$ 51,00" in r.json()["detail"]
    r = cliente.post(f"{url}/confirmar", headers=davi, json=pedido | {"pagamentos": [
        {"forma_pagamento_id": c["formas"]["cartao_credito"], "valor": "51.00", "parcelas": 2}]})
    assert r.status_code == 200, r.text
    assert (r.json()["carne"], r.json()["a_prazo"]) == ([], "0.00")

    # bloqueado, só acerta para si à vista
    with banco() as db:
        rep = db.get(Representante, c["rep"])
        rep.bloqueado, rep.motivo_bloqueio = True, "Atrasou"
        db.commit()
    a, url = _abrir(cliente, c)
    cliente.post(f"{url}/itens", headers=davi, json={"item_transferencia_id": c["com_ele"]["Perfume Ficticio"]})
    a = cliente.put(url, headers=davi, json={"para": "representante", "parcelas": 2,
                                             "primeiro_vencimento": date.today().isoformat()}).json()
    assert (a["tipo_comissao"], a["percentual"], a["valor"]) == ("representante", "20.00", "96.00")
    r = cliente.post(f"{url}/confirmar", headers=davi, json=pedido)
    assert r.status_code == 422 and "bloqueado: para ele, só acerto à vista (Atrasou)" in r.json()["detail"]


def test_acerto_de_queima(banco, cliente, consignado):
    c, davi = consignado, consignado["davi"]
    a, url = _abrir(cliente, c)
    cliente.post(f"{url}/itens", headers=davi, json={"item_transferencia_id": c["com_ele"]["Perfume Ficticio"]})
    r = cliente.put(url, headers=davi, json={"para": "representante", "pagamento": "vista", "queima": True})
    assert r.status_code == 422 and "Perfume Ficticio não está em queima" in r.json()["detail"]
    r = cliente.put(url, headers=davi, json={"para": "cliente", "cliente_id": c["freguesa"], "queima": True})
    assert r.status_code == 422 and "só para o próprio representante" in r.json()["detail"]
    item = cliente.get(url, headers=davi).json()["itens"][0]
    cliente.put(f"{url}/itens/{item['id']}", headers=davi, json={"quantidade": "0"})
    a = cliente.put(url, headers=davi, json={"para": "representante", "pagamento": "vista", "queima": True}).json()
    # o preço de queima, e 5%
    a = cliente.post(f"{url}/itens", headers=davi, json={"item_transferencia_id": c["com_ele"]["Toalha Ficticia"], "quantidade": "2"}).json()
    assert ([(i["preco"], i["total"]) for i in a["itens"]], a["tipo_comissao"], a["percentual"], a["valor"]) == (
        [("20.00", "40.00")], "queima", "5.00", "38.00")
    r = cliente.post(f"{url}/itens", headers=davi, json={"item_transferencia_id": c["com_ele"]["Perfume Ficticio"]})
    assert r.status_code == 422
    # sem queima, volta para o preço da transferência
    a = cliente.put(url, headers=davi, json={"para": "representante", "pagamento": "vista"}).json()
    assert (a["itens"][0]["preco"], a["valor"]) == ("30.00", "45.00")
    assert cliente.delete(url, headers=davi).status_code == 204


def test_comissoes_do_acerto_na_ficha(cliente, cenario, consignado):
    ficha = cliente.get(f"/representantes/{consignado['rep']}", headers=consignado["admin"]).json()
    assert [(x["tipo_cobranca"], x["percentual_padrao"]) for x in ficha["comissoes"]][-4:] == [
        ("vista_dinheiro", "25.00"), ("vista_cartao", "20.00"), ("vista_parcelado", "15.00"), ("queima", "5.00")]
    # sem a permissão, não acerta
    ana = _auth(cliente, "ana", cenario["e1"])
    assert cliente.post("/consignacao/acertos", headers=ana, json={"representante_id": consignado["rep"]}).status_code in (401, 403)
