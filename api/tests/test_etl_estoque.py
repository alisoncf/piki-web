"""ETL do estoque de uma loja (D24). Dados fictícios."""
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.empresas.esquemas import EmpresaNova
from app.dominios.empresas.servico import criar_empresa
from app.dominios.estoque.modelos import Estoque, MovimentoEstoque
from app.dominios.produtos.modelos import Produto
from etl.estoque import importar_estoque, mesmo_produto
from etl.funcionarios import EmpresaNaoImportada


def _banco_vb6(caminho, produtos, consignacoes=None):
    eng = create_engine(f"sqlite:///{caminho}")
    with eng.begin() as c:
        c.execute(text("""CREATE TABLE tab_produtos (cod_pro TEXT, nome_pro TEXT, ef_pro REAL, er_pro REAL, r_pro REAL,
            endereco_pro TEXT, cst_icms TEXT, cfop_pro TEXT)"""))
        for cod, nome, ef, endereco in produtos:
            c.execute(text("INSERT INTO tab_produtos VALUES (:c, :n, :ef, 0, 99, :e, '102', '5102')"),
                      {"c": cod, "n": nome, "ef": ef, "e": endereco})
        if consignacoes is not None:
            c.execute(text("CREATE TABLE tab_consignacoes (cod_pro TEXT, reman_con REAL)"))
            for cod, resto in consignacoes:
                c.execute(text("INSERT INTO tab_consignacoes VALUES (:c, :r)"), {"c": cod, "r": resto})
    return eng


@pytest.fixture
def empresa(banco):
    with banco() as db:
        e = criar_empresa(db, EmpresaNova(codigo="01", nome="MATRIZ"))
        db.add_all([Produto(codigo=1, nome="JOGO DE CAMA CASAL FICTICIO"), Produto(codigo=2, nome="TOALHA FICTICIA"),
                    Produto(codigo=3, nome="TAPETE FICTICIO 1.50/2.00")])
        db.commit()
        return e.id


def _importar(eng, banco):
    with eng.connect() as c, banco() as db:
        return importar_estoque(c, db, "01")


def test_mesmo_produto():
    assert mesmo_produto("FRIGIDEIRA 24 CM WOLFF", "FRIGIDEIRA 24 CM WOLFF##")
    assert mesmo_produto("TOALHA MESA 0.78/0.78 KARSTEN", "TOALHA MESA 0.78/0.78 KARSTEN/PINHEIRO")
    assert not mesmo_produto("COBERTOR QUEEN CONFORT 300 MAFRATEX", "COBERTOR CASAL SUBLIME JOLITEX")


def test_empresa_precisa_existir(banco, tmp_path):
    eng = _banco_vb6(tmp_path / "e.db", [])
    with pytest.raises(EmpresaNaoImportada):
        _importar(eng, banco)
    eng.dispose()


def test_importa_saldo_reservado_e_localizacao(banco, empresa, tmp_path):
    eng = _banco_vb6(tmp_path / "e01.db", [
        ("00000001", "JOGO DE CAMA CASAL FICTICIO", 10, "PRATELEIRA 2"),
        ("00000002", "TOALHA FICTICIA", 0, "UN"),  # nada: não ganha linha
        ("00000003", "COBERTOR DIFERENTE QUALQUER", 5, ""),  # outro produto com o código da matriz
        ("00000099", "SO NESTA LOJA", -2, ""),
    ], consignacoes=[("00000001", 3), ("00000001", 1), ("00000002", 0)])
    r = _importar(eng, banco)
    assert (r.linhas, r.movimentos, r.ignorados) == (1, 1, 2)
    assert any("00000003" in a and "na matriz é TAPETE" in a for a in r.avisos)
    assert any("00000099" in a and "não existe na matriz" in a for a in r.avisos)
    with banco() as db:
        e = db.scalar(select(Estoque))
        assert (e.quantidade, e.reservado, e.localizacao, e.cst_csosn, e.cfop) == (
            Decimal(10), Decimal(4), "PRATELEIRA 2", "102", "5102")
        m = db.scalar(select(MovimentoEstoque))
        assert (m.tipo, m.quantidade, m.reservado, m.saldo, m.saldo_reservado) == ("importacao", 10, 4, 10, 4)

    # na reimportação, só a diferença
    with eng.begin() as c:
        c.execute(text("UPDATE tab_produtos SET ef_pro = 7 WHERE cod_pro = '00000001'"))
    r = _importar(eng, banco)
    assert (r.linhas, r.movimentos) == (0, 1)
    with banco() as db:
        ultimo = db.scalars(select(MovimentoEstoque).order_by(MovimentoEstoque.id.desc())).first()
        assert (ultimo.quantidade, ultimo.reservado, ultimo.saldo) == (-3, 0, 7)
    eng.dispose()


def test_sem_tabela_de_consignacoes(banco, empresa, tmp_path):
    eng = _banco_vb6(tmp_path / "e02.db", [("00000001", "JOGO DE CAMA CASAL FICTICIO", -1, None)])
    r = _importar(eng, banco)
    assert (r.linhas, r.negativos) == (1, 1)
    with banco() as db:
        assert db.scalar(select(Estoque.reservado)) == 0
    eng.dispose()
