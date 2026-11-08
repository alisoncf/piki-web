"""Comissões do acerto (D30): o relatório do que ficou liberado no vencimento, o pagamento ao representante, que sai do
caixa e deixa saldo, e o histórico do VB6. Dados fictícios."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.acesso import repositorio
from app.dominios.acesso import servico as acesso
from app.dominios.caixa.modelos import LancamentoCaixa
from app.dominios.clientes.modelos import Cliente
from app.dominios.consignacao.modelos import BaixaComissao, ComissaoParcela, PagamentoComissao, Representante
from app.dominios.empresas.modelos import Empresa
from app.nucleo.legado import MapaLegado
from etl.comissoes import importar_comissoes
from tests.test_transferencias import _auth

HOJE = date.today()
ONTEM = HOJE - timedelta(days=1)
AMANHA = HOJE + timedelta(days=1)


@pytest.fixture
def comissoes(banco, cliente, cenario):
    """O representante 7 com comissões de R$ 30 (há um mês), R$ 40 (ontem) e R$ 50 (amanhã), o caixa aberto e a Ana
    podendo pagar."""
    admin = _auth(cliente, "caio", cenario["e1"])
    formas = {d["tipo"]: cliente.post("/formas-pagamento", headers=admin, json=d).json()["id"] for d in [
        {"nome": "Dinheiro", "tipo": "dinheiro"}, {"nome": "Crediário", "tipo": "crediario", "parcelas": 10, "parcelas_sem_autorizacao": 6}]}
    with banco() as db:
        maria = Cliente(nome="Maria Ficticia", cpf_cnpj="52998224725")
        db.add(maria)
        db.flush()
        rep = Representante(codigo=7, cliente_id=maria.id)
        db.add(rep)
        db.flush()
        for ordem, (vencimento, valor) in enumerate([(HOJE - timedelta(days=30), "30.00"), (ONTEM, "40.00"), (AMANHA, "50.00")], start=1):
            db.add(ComissaoParcela(empresa_id=cenario["e1"], representante_id=rep.id, vencimento=vencimento,
                                   valor=Decimal(valor), pago=Decimal("0.00"), legado=f"000000{ordem}",
                                   acerto_legado="0000009", cliente_legado="Freguesa Ficticia", parcela_legado=f"{ordem}/3"))
        perfil = acesso.criar_perfil(db, "Comissões", ["consignacao.pagar_comissao"])
        acesso.dar_acesso(db, repositorio.usuario_por_login(db, "davi"), db.get(Empresa, cenario["e1"]), perfil)
        db.commit()
        rep_id = rep.id
    caixa = cliente.post("/caixas", headers=admin, json={"nome": "Consignado"}).json()
    sessao = cliente.post(f"/caixas/{caixa['id']}/abrir", headers=admin, json={"fundo": "0"}).json()
    davi = _auth(cliente, "davi", cenario["e1"])
    return {"rep": rep_id, "davi": davi, "formas": formas, "sessao": sessao["id"], "url": f"/representantes/{rep_id}/comissoes"}


def _pagar(cliente, c, valor, **extra):
    return cliente.post(f"{c['url']}/pagamentos", headers=c["davi"], json={
        "valor": valor, "forma_pagamento_id": c["formas"]["dinheiro"], "sessao_caixa_id": c["sessao"]} | extra)


def test_libera_no_vencimento_e_o_pagamento_parcial_deixa_saldo(banco, cliente, comissoes):
    c = comissoes
    r = cliente.get(c["url"], headers=c["davi"]).json()
    assert (r["comissao"], r["pago"], r["liberado"], r["a_vencer"], r["quantas"]) == ("120.00", "0.00", "70.00", "50.00", 3)
    assert [(x["parcela"], x["liberada"], x["situacao"]) for x in r["linhas"]] == [("1/3", True, "aberta"), ("2/3", True, "aberta"), ("3/3", False, "aberta")]

    resposta = _pagar(cliente, c, "70.01")
    assert resposta.status_code == 422 and "passa do saldo liberado" in resposta.json()["detail"]

    pagamento = _pagar(cliente, c, "45.00")
    assert pagamento.status_code == 201
    r = cliente.get(c["url"], headers=c["davi"]).json()
    assert (r["pago"], r["liberado"], r["quantas"]) == ("45.00", "25.00", 2)
    assert [(x["parcela"], x["pago"], x["situacao"]) for x in r["linhas"]] == [("2/3", "15.00", "parcial"), ("3/3", "0.00", "aberta")]
    todas = cliente.get(c["url"], headers=c["davi"], params={"so_abertas": False}).json()
    assert [x["situacao"] for x in todas["linhas"]] == ["paga", "parcial", "aberta"]

    with banco() as db:
        lancamento = db.scalar(select(LancamentoCaixa).where(LancamentoCaixa.motivo == "comissao_consignado"))
        assert (lancamento.tipo, lancamento.valor, lancamento.sessao_id) == ("saida", Decimal("45.00"), c["sessao"])
        assert lancamento.documento == f"comissão {pagamento.json()['id']}"

    comprovante = cliente.get(f"/consignacao/comissoes/pagamentos/{pagamento.json()['id']}", headers=c["davi"]).json()
    assert [(x["parcela"], x["baixado"]) for x in comprovante["linhas"]] == [("1/3", "30.00"), ("2/3", "15.00")]
    assert comprovante["representante"]["codigo"] == 7


def test_o_pagamento_so_baixa_o_periodo_do_relatorio(cliente, comissoes):
    c = comissoes
    assert cliente.get(c["url"], headers=c["davi"], params={"de": ONTEM.isoformat()}).json()["liberado"] == "40.00"
    resposta = _pagar(cliente, c, "40.01", de=ONTEM.isoformat())
    assert resposta.status_code == 422 and "R$ 40,00" in resposta.json()["detail"].replace("\xa0", " ")
    assert _pagar(cliente, c, "40.00", de=ONTEM.isoformat()).status_code == 201
    r = cliente.get(c["url"], headers=c["davi"]).json()
    assert [x["parcela"] for x in r["linhas"]] == ["1/3", "3/3"]


def test_so_em_dinheiro_pix_ou_deposito_e_com_o_caixa_aberto(cliente, comissoes):
    c = comissoes
    resposta = _pagar(cliente, c, "10.00", forma_pagamento_id=c["formas"]["crediario"])
    assert resposta.status_code == 422 and "dinheiro, PIX ou depósito" in resposta.json()["detail"]
    assert _pagar(cliente, c, "10.00", sessao_caixa_id=9999).status_code == 422


def test_desfazer_o_pagamento_devolve_o_saldo(banco, cliente, cenario, comissoes):
    c = comissoes
    pagamento = _pagar(cliente, c, "45.00").json()
    url = f"/consignacao/comissoes/pagamentos/{pagamento['id']}/estornar"
    desfeito = cliente.post(url, headers=c["davi"])
    assert desfeito.status_code == 200 and desfeito.json()["estornado_em"]
    assert cliente.get(c["url"], headers=c["davi"]).json()["liberado"] == "70.00"
    with banco() as db:
        assert db.scalar(select(LancamentoCaixa).where(LancamentoCaixa.motivo == "comissao_consignado")).estornado_em
    assert cliente.post(url, headers=c["davi"]).status_code == 422

    # no caixa, o lançamento não se estorna sozinho
    outro = _pagar(cliente, c, "5.00").json()
    with banco() as db:
        lancamento_id = db.get(PagamentoComissao, outro["id"]).lancamento_id
    admin = _auth(cliente, "caio", cenario["e1"])
    assert cliente.post(f"/caixas/sessoes/{c['sessao']}/lancamentos/{lancamento_id}/estornar", headers=admin).status_code == 422


def test_permissao(cliente, cenario, comissoes):
    c = comissoes
    bia = _auth(cliente, "bia", cenario["e1"])  # gerente, sem as permissões das comissões
    assert cliente.get(c["url"], headers=bia).status_code == 403
    assert _pagar(cliente, c | {"davi": bia}, "10.00").status_code == 403


# o histórico do VB6

def _banco_vb6(caminho, linhas):
    eng = create_engine(f"sqlite:///{caminho}")
    with eng.begin() as x:
        x.execute(text("""CREATE TABLE tab_comissparc (seq_itd TEXT, seq_ace TEXT, valor_com REAL, venc_com TEXT, status_com TEXT,
            cod_rep TEXT, tipo_com TEXT, seq_cai TEXT)"""))
        x.execute(text("CREATE TABLE tab_acertos (seq_ace TEXT, data_ace TEXT, cod_cli INTEGER)"))
        x.execute(text("CREATE TABLE tab_clientes (cod_cli INTEGER, nome_cli TEXT)"))
        x.execute(text("CREATE TABLE tab_itdoc (seq_itd TEXT, seq_doc TEXT, parcela_itd INTEGER, valor_itd REAL)"))
        x.execute(text("CREATE TABLE tab_doc (seq_doc TEXT, parcelas_doc INTEGER)"))
        x.execute(text("CREATE TABLE tab_cheques (seq_che TEXT, seq_doc TEXT, parc_che INTEGER, valor_che REAL)"))
        x.execute(text("CREATE TABLE tab_caixa (seq_cai TEXT, data_cai TEXT)"))
        x.execute(text("INSERT INTO tab_acertos VALUES ('0000009', '2024-01-05', 5)"))
        x.execute(text("INSERT INTO tab_clientes VALUES (5, 'FREGUESA FICTICIA')"))
        x.execute(text("INSERT INTO tab_doc VALUES ('D1', 3)"))
        x.execute(text("INSERT INTO tab_itdoc VALUES ('0000001', 'D1', 1, 100), ('0000002', 'D1', 2, 100), ('0000003', 'D1', 3, 100)"))
        x.execute(text("INSERT INTO tab_cheques VALUES ('0000004', 'D1', 2, 80)"))
        x.execute(text("INSERT INTO tab_caixa VALUES ('C1', '2024-03-01')"))
        for linha in linhas:
            x.execute(text("INSERT INTO tab_comissparc VALUES (:seq, '0000009', :valor, :venc, :status, '000262', :tipo, :cai)"), linha)
    return eng


def _linha(seq, valor, venc, status="1", tipo="1", cai=""):
    return {"seq": seq, "valor": valor, "venc": venc, "status": status, "tipo": tipo, "cai": cai}


def _importar(eng, banco):
    with eng.connect() as c, banco() as db:
        return importar_comissoes(c, db, "01")


@pytest.fixture
def representante_importado(banco, cenario):
    with banco() as db:
        maria = Cliente(nome="Maria Ficticia", cpf_cnpj="52998224725")
        db.add(maria)
        db.flush()
        rep = Representante(codigo=262, cliente_id=maria.id)
        db.add(rep)
        db.flush()
        db.add(MapaLegado(tabela="tab_representantes", empresa_id=cenario["e1"], codigo="000262", novo_id=rep.id))
        db.commit()
        return rep.id


def test_importa_todo_o_historico_e_reimporta_sem_repetir(banco, cenario, representante_importado, tmp_path):
    arquivo = tmp_path / "vb6.db"
    eng = _banco_vb6(arquivo, [
        _linha("0000001", 30, "2024-02-05", "2", cai="C1"),
        _linha("0000002", 30, "2024-03-05", "2", cai="C1"),
        _linha("0000003", 30, "2024-04-05"),
        _linha("0000004", -12.5, "2024-04-10", tipo="2"),
        _linha("0000005", 0, "2024-04-12", "2", cai="C1"),  # paga, de valor zero: não pode baixar de novo ao reimportar
    ])
    r = _importar(eng, banco)
    assert (r.novas, r.baixadas, r.pagamentos, r.em_aberto) == (5, 3, 1, 2)
    assert (r.valor_pago, r.valor_em_aberto) == (Decimal("60.00"), Decimal("17.50"))
    with banco() as db:
        linhas = {c.legado: c for c in db.scalars(select(ComissaoParcela))}
        assert (linhas["0000001"].situacao, linhas["0000003"].situacao) == ("paga", "aberta")
        assert (linhas["0000003"].parcela_legado, linhas["0000003"].cliente_legado, linhas["0000003"].valor_parcela_legado) == ("3/3", "Freguesa Ficticia", Decimal("100.00"))
        assert (linhas["0000004"].parcela_legado, linhas["0000004"].valor) == ("cheque 2/3", Decimal("-12.50"))
        assert linhas["0000003"].data_acerto_legado == date(2024, 1, 5)
        pagamento = db.scalar(select(PagamentoComissao))
        assert (pagamento.valor, pagamento.data_hora.date(), pagamento.legado) == (Decimal("60.00"), date(2024, 3, 1), "C1")
        assert len(list(db.scalars(select(BaixaComissao)))) == 3

    # a 0000003 foi paga no VB6 depois, junto de um lançamento já importado; rodar de novo não repete nada
    with eng.begin() as x:
        x.execute(text("UPDATE tab_comissparc SET status_com = '2', seq_cai = 'C1' WHERE seq_itd = '0000003'"))
    r = _importar(eng, banco)
    assert (r.novas, r.atualizadas, r.baixadas, r.pagamentos) == (0, 1, 1, 0)
    r = _importar(eng, banco)
    assert (r.novas, r.atualizadas, r.baixadas) == (0, 0, 0)
    with banco() as db:
        assert db.scalar(select(PagamentoComissao)).valor == Decimal("90.00")
        assert len(list(db.scalars(select(BaixaComissao)))) == 4
        assert db.scalar(select(ComissaoParcela).where(ComissaoParcela.legado == "0000003")).situacao == "paga"


def test_representante_nao_importado_fica_de_fora_com_aviso(banco, cenario, tmp_path):
    eng = _banco_vb6(tmp_path / "vb6.db", [_linha("0000001", 30, "2024-02-05")])
    r = _importar(eng, banco)
    assert (r.novas, r.sem_representante) == (0, 1)
    assert "representante 000262" in r.avisos[0]
