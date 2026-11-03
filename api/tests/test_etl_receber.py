"""ETL das contas a receber de clientes (D26). Dados fictícios."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.acesso import servico as acesso
from app.dominios.caixa.modelos import Caixa, SessaoCaixa
from app.dominios.clientes.modelos import Cliente
from app.dominios.empresas.esquemas import EmpresaNova
from app.dominios.empresas.servico import criar_empresa
from app.dominios.receber import servico as contas
from app.dominios.receber.modelos import ContaReceber, ItemRecebimento, RecebimentoCrediario
from app.nucleo.legado import MapaLegado
from etl.receber import importar_receber


def _banco_vb6(caminho, docs, parcelas):
    eng = create_engine(f"sqlite:///{caminho}")
    with eng.begin() as c:
        c.execute(text("""CREATE TABLE tab_doc (seq_doc TEXT, num_doc TEXT, tipo_doc TEXT, cod_ter TEXT, valor_doc REAL,
            data_doc TEXT, cod_usu TEXT, excluido_doc TEXT, historico_doc TEXT, esp_doc TEXT, tipo_ter TEXT)"""))
        c.execute(text("""CREATE TABLE tab_itdoc (seq_itd TEXT, seq_doc TEXT, valor_itd REAL, reman_itd REAL,
            vencini_itd TEXT, venc_itd TEXT, parcela_itd INTEGER, prejuizo_itd TEXT DEFAULT 'N', cod_cob TEXT DEFAULT '000',
            cod_tip TEXT DEFAULT '2')"""))
        c.execute(text("CREATE TABLE tab_contacob (cod_cob TEXT, nome_cob TEXT)"))
        c.execute(text("INSERT INTO tab_contacob VALUES ('000', 'GERAL'), ('023', 'PREJUIZO'), ('029', 'LUDMILA ADVOGADA')"))
        for d in docs:
            c.execute(text("INSERT INTO tab_doc VALUES (:seq, :num, 'R', :ter, :valor, '2026-05-10', '001', 'N', :hist, :esp, :tipo)"), d)
        for p in parcelas:
            c.execute(text("INSERT INTO tab_itdoc VALUES (:seq, :doc, :valor, :resto, :venc, :venc, :n, :prej, :cob, :tip)"),
                      {"prej": "N", "cob": "000", "tip": "2"} | p)
    return eng


def _parcela(seq, doc, n, resto, venc, valor=100):
    return {"seq": seq, "doc": doc, "n": n, "resto": resto, "venc": venc, "valor": valor}


@pytest.fixture
def lojas(banco):
    """Duas lojas, cada uma com o seu cliente importado (o cod_cli 5 na 01, o 7 na 02)."""
    with banco() as db:
        e1 = criar_empresa(db, EmpresaNova(codigo="01", nome="MATRIZ"))
        e2 = criar_empresa(db, EmpresaNova(codigo="02", nome="FILIAL"))
        ana, bia = Cliente(nome="Ana Ficticia"), Cliente(nome="Bia Ficticia")
        db.add_all([ana, bia])
        db.flush()
        db.add_all([MapaLegado(tabela="tab_clientes", empresa_id=e1.id, codigo="5", novo_id=ana.id),
                    MapaLegado(tabela="tab_clientes", empresa_id=e2.id, codigo="7", novo_id=bia.id)])
        db.commit()
        return {"e1": e1.id, "e2": e2.id, "ana": ana.id, "bia": bia.id}


def _importar(eng, banco, codigo):
    with eng.connect() as c, banco() as db:
        return importar_receber(c, db, codigo)


def test_importa_as_contas_de_cada_loja_mesmo_com_o_mesmo_numero(banco, lojas, tmp_path):
    # as duas lojas têm o documento 0000100 (cada uma com a sua sequência), de clientes diferentes
    matriz = _banco_vb6(tmp_path / "m.db", [
        {"seq": "0000100", "num": "0000777", "ter": "000005", "valor": 300, "hist": "VENDA 0000777 ANA", "esp": "V", "tipo": "C"},
        {"seq": "0000101", "num": "0000778", "ter": "000003", "valor": 50, "hist": "REPRESENTANTE", "esp": "A", "tipo": "R"},
        {"seq": "0000102", "num": "0000779", "ter": "000099", "valor": 80, "hist": "SEM CLIENTE", "esp": "V", "tipo": "C"},
        {"seq": "0000103", "num": "0000780", "ter": "000005", "valor": 100, "hist": "QUITADA", "esp": "V", "tipo": "C"},
    ], [
        _parcela("0000500", "0000100", 1, 0, "2026-06-10") | {"tip": "1"},  # paga: entra para o carnê continuar "2 de 3"
        _parcela("0000501", "0000100", 2, 100, "2026-07-10") | {"cob": "029"},  # com a advogada
        _parcela("0000502", "0000100", 3, 100, "2026-08-10") | {"cob": "023"},  # na conta de cobrança PREJUIZO
        _parcela("0000503", "0000101", 1, 50, "2026-06-10", 50),
        _parcela("0000504", "0000102", 1, 80, "2026-06-10", 80),
        _parcela("0000505", "0000103", 1, 0, "2026-06-10"),  # tudo pago: não entra
    ])
    filial = _banco_vb6(tmp_path / "f.db", [
        {"seq": "0000100", "num": "0000777", "ter": "000007", "valor": 120, "hist": "MIGR. CONS. 000087", "esp": "A", "tipo": "C"},
    ], [
        _parcela("0000500", "0000100", 1, 60, "2026-06-10", 60),
        _parcela("0000501", "0000100", 2, 60, "2026-07-10", 60),
    ])

    r = _importar(matriz, banco, "01")
    assert (r.contas, r.parcelas, r.parcelas_em_aberto, r.em_aberto, r.sem_cliente) == (1, 3, 2, Decimal("200.00"), 1)
    assert (r.prejuizo, r.em_prejuizo) == (1, Decimal("100.00"))
    assert r.fora == ["1 parcelas em aberto de representantes (50.00), que não entram aqui"]
    r = _importar(filial, banco, "02")
    assert (r.contas, r.parcelas, r.em_aberto) == (1, 2, Decimal("120.00"))

    with banco() as db:
        ana = db.scalar(select(ContaReceber).where(ContaReceber.cliente_id == lojas["ana"]))
        bia = db.scalar(select(ContaReceber).where(ContaReceber.cliente_id == lojas["bia"]))
        assert (ana.documento, ana.origem, ana.valor, ana.criado_em.date()) == ("01-0000777", "venda", Decimal("300.00"), date(2026, 5, 10))
        assert (bia.documento, bia.origem) == ("02-0000777", "acerto")  # mesmo número, outra loja, outra conta
        assert [(p.numero, p.aberto) for p in ana.parcelas] == [(1, 0), (2, 100), (3, 100)]
        assert [p.prejuizo_motivo for p in ana.parcelas] == [None, None, "No VB6: conta de cobrança PREJUIZO"]
        assert [p.conta_cobranca.nome for p in ana.parcelas] == ["Geral", "Ludmila Advogada", "Geral"]
        assert [p.tipo_cobranca for p in ana.parcelas] == ["loja", "cliente", "cliente"]
        assert contas.em_aberto(db, lojas["ana"]) == Decimal("200.00")


def test_reimportar_acompanha_o_vb6_menos_o_que_ja_foi_recebido_aqui(banco, lojas, tmp_path):
    docs = [{"seq": "0000100", "num": "0000777", "ter": "000005", "valor": 200, "hist": "VENDA", "esp": "V", "tipo": "C"}]
    _importar(_banco_vb6(tmp_path / "a.db", docs, [
        _parcela("0000500", "0000100", 1, 100, "2026-06-10"), _parcela("0000501", "0000100", 2, 100, "2026-07-10")]),
        banco, "01")
    with banco() as db:  # a segunda parcela foi recebida no sistema novo
        caixa = Caixa(empresa_id=lojas["e1"], nome="Cx 02")
        db.add(caixa)
        db.flush()
        usuario = acesso.criar_usuario(db, "caio", "Caio Ficticio", "senha-caio")
        sessao = SessaoCaixa(caixa_id=caixa.id, aberto_por_id=usuario.id)
        db.add(sessao)
        db.flush()
        segunda = db.scalar(select(ContaReceber)).parcelas[1]
        segunda.aberto = Decimal("0.00")
        db.add(RecebimentoCrediario(empresa_id=lojas["e1"], sessao_caixa_id=sessao.id, cliente_id=lojas["ana"],
                                    usuario_id=usuario.id,
                                    itens=[ItemRecebimento(parcela=segunda, valor=Decimal("100.00"), juros=Decimal(0))]))
        db.commit()
    # no VB6, a primeira foi paga depois da importação (o documento nem aparece mais como aberto),
    # e a segunda mudou de vencimento lá
    r = _importar(_banco_vb6(tmp_path / "b.db", docs, [
        _parcela("0000500", "0000100", 1, 0, "2026-06-10"), _parcela("0000501", "0000100", 2, 100, "2026-09-10")]),
        banco, "01")
    assert (r.contas, r.parcelas, r.atualizadas) == (0, 0, 1)
    assert "já recebida no sistema novo" in r.avisos[0]
    with banco() as db:
        primeira, segunda = db.scalar(select(ContaReceber)).parcelas
        assert (primeira.aberto, segunda.aberto, segunda.vencimento) == (0, 0, date(2026, 7, 10))
