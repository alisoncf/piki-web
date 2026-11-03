"""Formas de pagamento e caixa (D26). Dados fictícios."""
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.caixa.modelos import Caixa, FormaPagamento
from app.dominios.empresas.modelos import Empresa
from app.dominios.funcionarios.modelos import Funcionario
from etl import mapa
from etl.caixa import importar_caixa


def _auth(cliente, login, empresa_id):
    r = cliente.post("/auth/login", json={"login": login, "senha": f"senha-{login}", "empresa_id": empresa_id})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(cliente, cenario):
    return _auth(cliente, "caio", cenario["e1"])


@pytest.fixture
def operador(banco, cliente, cenario):
    """O davi opera o caixa da empresa 01, sem ver o saldo esperado."""
    with banco() as db:
        perfil = acesso.criar_perfil(db, "Caixa", ["caixa.operar"])
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "davi"), db.get(Empresa, cenario["e1"]), perfil)
    return _auth(cliente, "davi", cenario["e1"])


@pytest.fixture
def formas(cliente, admin):
    dinheiro = cliente.post("/formas-pagamento", headers=admin, json={"nome": "Dinheiro", "tipo": "dinheiro", "desconto": "5"}).json()
    pix = cliente.post("/formas-pagamento", headers=admin, json={"nome": "PIX", "tipo": "pix", "ordem": 2}).json()
    return {"dinheiro": dinheiro["id"], "pix": pix["id"]}


def test_formas_de_pagamento(cliente, admin, formas):
    r = cliente.post("/formas-pagamento", headers=admin, json={
        "nome": "Crediário", "tipo": "crediario", "parcelas": 10, "parcelas_sem_autorizacao": 6})
    assert r.status_code == 201 and (r.json()["codigo_nfce"], r.json()["parcelas_sem_autorizacao"]) == ("05", 6)
    # o "sem autorização" nunca passa do máximo
    r = cliente.put(f"/formas-pagamento/{r.json()['id']}", headers=admin, json={
        "nome": "Crediário", "tipo": "crediario", "parcelas": 4, "parcelas_sem_autorizacao": 6})
    assert r.json()["parcelas_sem_autorizacao"] == 4
    assert cliente.post("/formas-pagamento", headers=admin, json={"nome": "pix", "tipo": "pix"}).status_code == 409
    assert cliente.post("/formas-pagamento", headers=admin, json={"nome": "Cheque", "tipo": "cheque"}).status_code == 422
    assert [f["nome"] for f in cliente.get("/formas-pagamento", headers=admin).json()] == ["Crediário", "Dinheiro", "PIX"]  # pela ordem, depois pelo nome


def test_abrir_lancar_e_fechar(banco, cliente, cenario, admin, operador, formas):
    with banco() as db:
        funcionario = Funcionario(nome="Laura Ficticia", empresa_id=cenario["e1"])
        db.add(funcionario)
        db.commit()
        funcionario_id = funcionario.id
    caixa = cliente.post("/caixas", headers=admin, json={"nome": "Cx 02"}).json()
    assert cliente.post("/caixas", headers=admin, json={"nome": "cx 02"}).status_code == 409
    assert cliente.post("/caixas", headers=operador, json={"nome": "Cx 09"}).status_code == 403

    r = cliente.post(f"/caixas/{caixa['id']}/abrir", headers=operador, json={"fundo": "100"})
    assert r.status_code == 201, r.text
    sessao = r.json()
    assert (sessao["situacao"], sessao["aberto_por"]["nome"], sessao["totais"]) == ("aberto", "Davi Sem Acesso", None)
    assert cliente.post(f"/caixas/{caixa['id']}/abrir", headers=admin, json={}).status_code == 422  # já aberto
    assert cliente.get("/caixas", headers=operador).json()[0]["sessao"]["id"] == sessao["id"]

    url = f"/caixas/sessoes/{sessao['id']}"
    lancar = lambda dados, quem=operador: cliente.post(f"{url}/lancamentos", headers=quem, json=dados)  # noqa: E731
    assert lancar({"motivo": "suprimento", "valor": "50"}).json()["forma_pagamento"]["nome"] == "Dinheiro"
    # a despesa e a outra entrada levam a conta do plano de contas, do tipo certo
    lanche = cliente.post("/plano-contas", headers=admin, json={"tipo": "despesa", "nome": "Lanches"}).json()
    diversas = cliente.post("/plano-contas", headers=admin, json={"tipo": "receita", "nome": "Receitas diversas"}).json()
    assert cliente.post("/plano-contas", headers=admin, json={"tipo": "despesa", "nome": "lanches"}).status_code == 409
    assert lancar({"motivo": "despesa", "valor": "12.50", "historico": "Pão"}).status_code == 422  # sem a conta
    r = lancar({"motivo": "despesa", "valor": "12.50", "historico": "Pão", "plano_conta_id": diversas["id"]})
    assert r.status_code == 422 and "não é uma conta de despesa" in r.json()["detail"]
    r = lancar({"motivo": "despesa", "valor": "12.50", "historico": "Pão", "plano_conta_id": lanche["id"]})
    assert r.status_code == 201 and r.json()["plano_conta"]["nome"] == "Lanches"
    assert lancar({"motivo": "despesa", "valor": "1"}).status_code == 422  # sem dizer do que é
    assert lancar({"motivo": "vale", "valor": "30"}).status_code == 422  # sem funcionário
    vale = lancar({"motivo": "vale", "valor": "30", "funcionario_id": funcionario_id}).json()
    assert (vale["tipo"], vale["funcionario"]["nome"]) == ("saida", "Laura Ficticia")
    assert lancar({"motivo": "outra_entrada", "valor": "80", "forma_pagamento_id": formas["pix"], "historico": "Acerto",
                   "plano_conta_id": diversas["id"]}).status_code == 201
    errado = lancar({"motivo": "sangria", "valor": "999"}).json()
    r = cliente.post(f"{url}/lancamentos/{errado['id']}/estornar", headers=operador)
    assert r.json()["estornado_por"]["nome"] == "Davi Sem Acesso"
    assert cliente.post(f"{url}/lancamentos/{errado['id']}/estornar", headers=operador).status_code == 422

    # quem confere vê o saldo esperado; o operador não (conferência cega)
    assert cliente.get(url, headers=operador).json()["totais"] is None
    totais = {t["forma_pagamento"]["nome"]: t["saldo"] for t in cliente.get(url, headers=admin).json()["totais"]}
    assert totais == {"Dinheiro": "107.50", "PIX": "80.00"}  # 100 + 50 − 12,50 − 30

    r = cliente.post(f"{url}/fechar", headers=operador, json={
        "contagem": [{"forma_pagamento_id": formas["dinheiro"], "contado": "105"}], "observacao": "Faltou troco"})
    assert r.status_code == 200, r.text
    fechada = r.json()
    assert (fechada["situacao"], fechada["fechado_por"]["nome"], fechada["observacao"]) == ("fechado", "Davi Sem Acesso", "Faltou troco")
    assert {c["forma_pagamento"]["nome"]: c["diferenca"] for c in fechada["conferencia"]} == {
        "Dinheiro": "-2.50", "PIX": "-80.00"}  # o PIX não contado conta como zero
    assert fechada["totais"] is not None  # depois de fechado, aparece para quem fechou
    assert lancar({"motivo": "suprimento", "valor": "1"}).status_code == 422
    assert cliente.get("/caixas", headers=operador).json()[0]["sessao"] is None

    assert cliente.get(f"/caixas/{caixa['id']}/sessoes", headers=operador).status_code == 403
    assert cliente.get(f"/caixas/{caixa['id']}/sessoes", headers=admin).json()["total"] == 1
    # outra loja não vê o caixa
    outra = _auth(cliente, "caio", cenario["e2"])
    assert cliente.get(url, headers=outra).status_code == 404
    assert cliente.get("/caixas", headers=outra).json() == []


def test_sem_forma_dinheiro(cliente, admin):
    caixa = cliente.post("/caixas", headers=admin, json={"nome": "Cx 02"}).json()
    r = cliente.post(f"/caixas/{caixa['id']}/abrir", headers=admin, json={})
    assert r.status_code == 422 and "Dinheiro" in r.json()["detail"]  # o fundo de troco é em dinheiro


def test_etl_formas_e_caixas(banco, cenario, tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'c.db'}")
    with eng.begin() as c:
        c.execute(text("""CREATE TABLE tab_formaspag (cod_for TEXT, nome_for TEXT, desconto_for REAL, tipo_cai TEXT,
            avista_for TEXT, parcelas_for INTEGER, intervalo_for INTEGER, gerencial_for TEXT, visivel_for TEXT)"""))
        for linha in [("01", "DINHEIRO", 5, "DIN", 1, "N"), ("06", "1X DUP", 0, "DUP", 1, "N"), ("13", "6X DUP", 0, "DUP", 6, "N"),
                      ("20", "10X DUP", 0, "DUP", 10, "S"), ("04", "2X CHEQUE", 0, "CHP", 2, "N"), ("99", "ESQUISITA", 0, "XXX", 1, "N")]:
            c.execute(text("INSERT INTO tab_formaspag VALUES (:c, :n, :d, :t, 'S', :p, 30, :g, 'S')"),
                      dict(zip("cndtpg", linha)))
        c.execute(text("CREATE TABLE tab_parametros (juros_par REAL)"))
        c.execute(text("INSERT INTO tab_parametros VALUES (5)"))
        c.execute(text("CREATE TABLE tab_caixas (cod_cai TEXT, nome_cai TEXT, status_cai TEXT)"))
        for linha in [("00", "SEM CAIXA", "A"), ("02", "Cx 02", "A"), ("05", "Crediário", "A")]:
            c.execute(text("INSERT INTO tab_caixas VALUES (:c, :n, :s)"), dict(zip("cns", linha)))
    with eng.connect() as c, banco() as db:
        r = importar_caixa(c, db, "01")
        assert (r.formas, r.caixas) == (3, 3) and "XXX" in r.avisos[0]
        crediario = db.scalar(select(FormaPagamento).where(FormaPagamento.tipo == "crediario"))
        assert (crediario.nome, crediario.parcelas, crediario.parcelas_sem_autorizacao) == ("Crediário", 10, 6)
        assert crediario.juros_atraso == Decimal("5.00")  # o juros_par da loja
        assert db.scalar(select(FormaPagamento).where(FormaPagamento.nome == "Cheque")).ativo is False
        # todos os códigos de crediário apontam para a mesma forma
        assert {mapa.buscar(db, "tab_formaspag", cenario["e1"], c) for c in ("06", "13", "20")} == {crediario.id}
        caixas = {x.nome: x.ativo for x in db.scalars(select(Caixa))}
        assert caixas == {"Sem caixa": False, "Cx 02": True, "Crediário": True}
        assert importar_caixa(c, db, "01").formas == 0  # reimportar não duplica
    eng.dispose()
