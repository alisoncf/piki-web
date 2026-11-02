"""ETL de produtos (D24). Dados fictícios: nada de dado real no repositório."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.empresas.esquemas import EmpresaNova
from app.dominios.empresas.servico import criar_empresa
from app.dominios.fornecedores.modelos import Fornecedor
from app.dominios.produtos.modelos import CodigoBarras, Produto, Secao, Subsecao
from etl import mapa
from etl.funcionarios import EmpresaNaoImportada
from etl.produtos import importar_produtos, nome_da_secao, unidade

HOJE = date(2026, 11, 2)

_DDL = [
    "CREATE TABLE tab_secoes (cod_sec TEXT, nome_sec TEXT)",
    "CREATE TABLE tab_subsec (cod_sub TEXT, nome_sub TEXT, cod_sec TEXT)",
    """CREATE TABLE tab_produtos (cod_pro TEXT, nome_pro TEXT, cod_sub TEXT, cr_pro REAL, cf_pro REAL, pv_pro REAL,
        pa_pro REAL, pq_pro REAL, lucro_pro REAL, unidade_pro TEXT, fracionado_pro TEXT, cod_fab INTEGER, ncm_pro TEXT,
        cest_pro TEXT, cod_ori TEXT, dataalt_pro TEXT, ean_pro TEXT, codbarra_pro TEXT)""",
    "CREATE TABLE tab_codbarras (cod_pro TEXT, cod_bar TEXT)",
    "CREATE TABLE tab_vendas (num_ven TEXT, data_ven TEXT, situacao_ven TEXT)",
    "CREATE TABLE tab_itvendas (num_ven TEXT, cod_pro TEXT, qtd_ite REAL)",
    "CREATE TABLE tab_compras (seq_not TEXT, entrada_not TEXT)",
    "CREATE TABLE tab_itcompras (seq_not TEXT, cod_pro TEXT)",
]

_PRODUTO = {
    "cod_pro": "00000001", "nome_pro": "JOGO DE CAMA CASAL  FICTICIO", "cod_sub": "005", "cr_pro": 40.0,
    "cf_pro": 45.5, "pv_pro": 99.0, "pa_pro": 99.0, "pq_pro": 0.0, "lucro_pro": 30.0, "unidade_pro": "UN",
    "fracionado_pro": "N", "cod_fab": 5, "ncm_pro": "6302.31.00", "cest_pro": None, "cod_ori": "0",
    "dataalt_pro": "2020-01-10", "ean_pro": "SEM GTIN", "codbarra_pro": "SEM GTIN",
}


def _inserir(c, tabela, linha):
    c.execute(text(f"INSERT INTO {tabela} ({', '.join(linha)}) VALUES ({', '.join(':' + k for k in linha)})"), linha)


def _banco_vb6(caminho, produtos=(), barras=(), vendas=(), compras=()):
    eng = create_engine(f"sqlite:///{caminho}")
    with eng.begin() as c:
        for ddl in _DDL:
            c.execute(text(ddl))
        for cod, nome in (("001", "CAMA)</item"), ("002", "MESA"), ("", None)):
            _inserir(c, "tab_secoes", {"cod_sec": cod, "nome_sec": nome})
        for cod, nome, sec in (("005", "JOGO DE CAMA", "001"), ("012", "TOALHA DE MESA", "002"), ("029", "LENCOS", "000")):
            _inserir(c, "tab_subsec", {"cod_sub": cod, "nome_sub": nome, "cod_sec": sec})
        for p in produtos:
            _inserir(c, "tab_produtos", {**_PRODUTO, **p})
        for cod, barra in barras:
            _inserir(c, "tab_codbarras", {"cod_pro": cod, "cod_bar": barra})
        for i, (cod, data, qtd, situacao) in enumerate(vendas):
            _inserir(c, "tab_vendas", {"num_ven": str(i), "data_ven": data, "situacao_ven": situacao})
            _inserir(c, "tab_itvendas", {"num_ven": str(i), "cod_pro": cod, "qtd_ite": qtd})
        for i, (cod, data) in enumerate(compras):
            _inserir(c, "tab_compras", {"seq_not": str(i), "entrada_not": data})
            _inserir(c, "tab_itcompras", {"seq_not": str(i), "cod_pro": cod})
    return eng


@pytest.fixture
def matriz(banco):
    """A empresa 01, com o fornecedor 5 do VB6 já importado."""
    with banco() as db:
        empresa = criar_empresa(db, EmpresaNova(codigo="01", nome="MATRIZ"))
        fornecedor = Fornecedor(nome="TECIDOS FICTICIOS LTDA", cpf_cnpj="11222333000181")
        db.add(fornecedor)
        db.flush()
        mapa.gravar(db, "tab_fornecedores", empresa.id, "5", fornecedor.id)
        db.commit()
        return fornecedor.id


def _importar(eng, banco, outras=()):
    with eng.connect() as c, banco() as db:
        conexoes = [o.connect() for o in outras]
        try:
            return importar_produtos(c, db, "01", conexoes, hoje=HOJE)
        finally:
            for o in conexoes:
                o.close()


def test_conversoes():
    assert nome_da_secao("CAMA)</item") == "CAMA"
    assert nome_da_secao(None) is None
    assert (unidade(" m2 "), unidade(","), unidade(None), unidade("JG")) == ("M2", "UN", "UN", "JG")


def test_empresa_precisa_existir(banco, tmp_path):
    eng = _banco_vb6(tmp_path / "p.db")
    with pytest.raises(EmpresaNaoImportada):
        _importar(eng, banco)
    eng.dispose()


def test_importa_produtos(banco, matriz, tmp_path):
    eng = _banco_vb6(tmp_path / "p01.db", produtos=[
        {},  # vendido há um mês: ativo
        {"cod_pro": "00000002", "nome_pro": "TOALHA DE MESA FICTICIA", "cod_sub": "012", "cf_pro": 0, "cr_pro": 12.0,
         "pv_pro": 30.0, "pq_pro": 19.9, "cod_fab": 0, "ncm_pro": "", "cod_ori": None},  # parada: inativa
        {"cod_pro": "00000003", "nome_pro": "PASSADEIRA FICTICIA M2", "cod_sub": "999", "unidade_pro": ",",
         "cod_fab": 77, "pq_pro": 200.0, "dataalt_pro": "0000-00-00"},  # vendida com fração na outra loja
        {"cod_pro": "00000004", "nome_pro": "PRODUTO NOVO FICTICIO", "dataalt_pro": "2026-10-01"},  # recém-cadastrado
        {"cod_pro": "00000005", "nome_pro": "COMPRADO FICTICIO"},  # só comprado
        {"cod_pro": "00000006", "nome_pro": "VENDA CANCELADA FICTICIA"},
    ], barras=[
        ("00000001", "00000001"),  # o próprio código: não vem
        ("00000001", "7891234567895"),
        ("00000002", "00000001"),  # código de outro produto: ambíguo
        ("00000002", "NULL)</item)</it"),
        ("00000002", "7899999999991"), ("00000004", "7899999999991"),  # repetido: fica no mais novo
    ], vendas=[
        ("00000001", "2026-10-01 10:00:00", 1, "4"),
        ("00000002", "2024-01-01 10:00:00", 1, "4"),
        ("00000006", "2026-10-01 10:00:00", 1, "5"),
    ], compras=[("00000005", "2026-03-01")])
    outra = _banco_vb6(tmp_path / "p02.db", vendas=[("00000003", "2026-09-01 10:00:00", 2.5, "4")])

    r = _importar(eng, banco, [outra])
    assert (r.secoes, r.subsecoes, r.criados, r.ativos, r.inativos) == (2, 3, 6, 4, 2)
    assert (r.fracionados, r.codigos_barras, r.fornecedores) == (1, 2, 4)
    assert any("subseção 029" in a and "DIVERSOS" in a for a in r.avisos)
    assert any("produto 3" in a and "fornecedor 77" in a for a in r.avisos)
    assert any("00000001 é o código de outro produto" in a for a in r.avisos)

    with banco() as db:
        p = {x.codigo: x for x in db.scalars(select(Produto))}
        assert (p[1].nome, p[1].custo, p[1].preco_venda, p[1].margem, p[1].ncm, p[1].ativo) == (
            "JOGO DE CAMA CASAL FICTICIO", Decimal("45.50"), Decimal("99.00"), Decimal("30.00"), "63023100", True)
        assert [c.codigo for c in p[1].codigos_barras] == ["7891234567895"]
        assert [f.fornecedor_id for f in p[1].fornecedores] == [matriz]
        assert p[1].subsecao.nome == "JOGO DE CAMA" and p[1].subsecao.secao.nome == "CAMA"
        # sem custo da nota, o custo real; queima abaixo do preço; parada há mais de um ano
        assert (p[2].custo, p[2].preco_queima, p[2].ncm, p[2].origem, p[2].ativo) == (
            Decimal("12.00"), Decimal("19.90"), None, 0, False)
        assert p[2].codigos_barras == []
        assert (p[3].subsecao_id, p[3].unidade, p[3].fracionado, p[3].preco_queima, p[3].ativo) == (None, "UN", True, None, True)
        assert [c.codigo for c in p[4].codigos_barras] == ["7899999999991"]
        assert (p[4].ativo, p[5].ativo, p[6].ativo) == (True, True, False)
        assert sorted(s.nome for s in db.scalars(select(Secao))) == ["CAMA", "DIVERSOS", "MESA"]

        # o que foi acrescentado no sistema novo fica na reimportação; o resto volta a ser o do VB6
        p[1].nome = "MUDADO"
        p[1].codigos_barras.append(CodigoBarras(codigo="7890000000001"))
        db.commit()

    r = _importar(eng, banco, [outra])
    assert (r.secoes, r.subsecoes, r.criados, r.atualizados, r.codigos_barras, r.fornecedores) == (0, 0, 0, 6, 0, 0)
    with banco() as db:
        p1 = db.scalar(select(Produto).where(Produto.codigo == 1))
        assert p1.nome == "JOGO DE CAMA CASAL FICTICIO"
        assert sorted(c.codigo for c in p1.codigos_barras) == ["7890000000001", "7891234567895"]
        assert db.scalar(select(Subsecao).where(Subsecao.nome == "LENCOS")).secao.nome == "DIVERSOS"
    eng.dispose()
    outra.dispose()
