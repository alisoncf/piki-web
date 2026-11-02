"""ETL de fornecedores (D22). Dados fictícios (CNPJs gerados só para teste): nada de dado real no repositório."""
import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.empresas.esquemas import EmpresaNova
from app.dominios.empresas.servico import criar_empresa
from app.dominios.fornecedores.modelos import Fornecedor
from etl import mapa
from etl.fornecedores import importar_fornecedores, separar_contato, telefone
from etl.funcionarios import EmpresaNaoImportada

CNPJ_A = "11222333000181"
CNPJ_B = "11444777000161"

_DDL = [
    """CREATE TABLE tab_fornecedores (
        COD_FOR INTEGER PRIMARY KEY, NOME_FOR TEXT, FANTASIA_FOR TEXT, CNPJ_FOR TEXT, ie_for TEXT, ENDERECO_FOR TEXT,
        BAIRRO_FOR TEXT, CIDADE_FOR TEXT, UF_FOR TEXT, CEP_FOR TEXT, TELEFONE_FOR TEXT, FAX_FOR TEXT, CONTATO_FOR TEXT,
        EMAIL_FOR TEXT, codantigo_for TEXT, obs_for TEXT, logradouro_for TEXT)""",
    "CREATE TABLE tab_telefones (cod_cli INTEGER, num_tel TEXT, tipo_tel TEXT, tipo_ter TEXT)",
]

_TECIDOS = {
    "COD_FOR": 1, "NOME_FOR": "TECIDOS FICTICIOS LTDA", "FANTASIA_FOR": "FICTICIA", "CNPJ_FOR": "11.222.333/0001-81",
    "ie_for": "25.753.510-1", "ENDERECO_FOR": "RUA DAS FLORES 100", "BAIRRO_FOR": "CENTRO", "CIDADE_FOR": "BLUMENAU",
    "UF_FOR": "SC", "CEP_FOR": "89010000", "TELEFONE_FOR": "(0..47)3333-4444", "FAX_FOR": "", "CONTATO_FOR": "RITA 9971-0002",
    "EMAIL_FOR": "VENDAS@FICTICIA.COM.BR", "obs_for": "ENTREGA NA SEGUNDA",
}


def _banco_vb6(caminho, fornecedores, telefones=()):
    eng = create_engine(f"sqlite:///{caminho}")
    with eng.begin() as c:
        for ddl in _DDL:
            c.execute(text(ddl))
        for linha in fornecedores:
            c.execute(text(f"INSERT INTO tab_fornecedores ({', '.join(linha)}) VALUES ({', '.join(':' + k for k in linha)})"),
                      linha)
        for cod, num, tipo, ter in telefones:
            c.execute(text("INSERT INTO tab_telefones VALUES (:c, :n, :t, :ter)"), {"c": cod, "n": num, "t": tipo, "ter": ter})
    return eng


@pytest.fixture
def empresas(banco):
    with banco() as db:
        e1 = criar_empresa(db, EmpresaNova(codigo="01", nome="MATRIZ"))
        e2 = criar_empresa(db, EmpresaNova(codigo="02", nome="FILIAL"))
        db.add_all([Cidade(codigo_ibge=c, nome=n, uf=uf, nome_busca=nome_de_busca(n)) for c, n, uf in (
            ("4202404", "Blumenau", "SC"), ("3545803", "Santa Bárbara d'Oeste", "SP"),
            ("3548708", "São Bernardo do Campo", "SP"))])
        db.commit()
        return {"01": e1.id, "02": e2.id}


def _importar(eng, banco, codigo):
    with eng.connect() as c, banco() as db:
        return importar_fornecedores(c, db, codigo)


def test_telefone_e_contato():
    assert telefone("(0..19)3807-7511") == "1938077511"
    assert telefone("(009)916-6993") == "99166993"
    assert telefone("3333") is None
    assert separar_contato("RITA 9971-0002") == ("RITA", "99710002")
    assert separar_contato("FAX15-3284-5809") == (None, "1532845809")
    assert separar_contato("JOAO E MARIA") == ("JOAO E MARIA", None)
    assert separar_contato("") == (None, None)


def test_empresa_precisa_existir(banco, tmp_path):
    eng = _banco_vb6(tmp_path / "f.db", [_TECIDOS])
    with pytest.raises(EmpresaNaoImportada):
        _importar(eng, banco, "01")
    eng.dispose()


def test_importa_descarta_e_junta_pelo_cnpj(banco, empresas, tmp_path):
    matriz = _banco_vb6(tmp_path / "f01.db", [
        _TECIDOS,
        {**_TECIDOS, "COD_FOR": 2, "NOME_FOR": "SEM CNPJ LTDA", "CNPJ_FOR": "11.222.333/0001-82"},
        {**_TECIDOS, "COD_FOR": 3, "NOME_FOR": "TESTE", "CNPJ_FOR": CNPJ_B},
        {**_TECIDOS, "COD_FOR": 4, "NOME_FOR": "TOALHAS EXEMPLO", "CNPJ_FOR": CNPJ_B, "CIDADE_FOR": "LUGAR NENHUM",
         "TELEFONE_FOR": "", "CONTATO_FOR": "FAX 47-3333-5555", "FANTASIA_FOR": ""},
    ], telefones=[(1, "47 99999-1111", "3", "F"), (1, "47 98888-0000", "3", "C")])  # o 'C' é de cliente
    r = _importar(matriz, banco, "01")
    assert (r.criados, r.descartados, r.telefones, r.contatos) == (2, 2, 3, 1)
    assert any("cidade LUGAR NENHUM/SC não encontrada" in a for a in r.avisos)
    with banco() as db:
        tecidos = db.scalar(select(Fornecedor).where(Fornecedor.cpf_cnpj == CNPJ_A))
        assert (tecidos.nome, tecidos.nome_fantasia, tecidos.inscricao_estadual) == ("TECIDOS FICTICIOS LTDA", "FICTICIA", "257535101")
        assert (tecidos.logradouro, tecidos.cep, tecidos.cidade.nome) == ("RUA DAS FLORES 100", "89010000", "Blumenau")
        assert (tecidos.email, tecidos.observacao) == ("vendas@ficticia.com.br", "ENTREGA NA SEGUNDA")
        assert [(t.numero, t.tipo) for t in tecidos.telefones] == [("4733334444", "2"), ("47999991111", "3")]
        assert [(c.nome, c.telefone) for c in tecidos.contatos] == [("RITA", "99710002")]
        toalhas = db.scalar(select(Fornecedor).where(Fornecedor.cpf_cnpj == CNPJ_B))
        assert (toalhas.nome, toalhas.cidade, toalhas.contatos) == ("TOALHAS EXEMPLO", None, [])
        assert [(t.numero, t.tipo) for t in toalhas.telefones] == [("4733335555", "5")]

    # a filial tem o mesmo fornecedor em outro código: junta pelo CNPJ e só completa (a matriz manda)
    filial = _banco_vb6(tmp_path / "f02.db", [
        {**_TECIDOS, "COD_FOR": 9, "NOME_FOR": "TECIDOS FICT LTDA", "obs_for": "", "BAIRRO_FOR": "",
         "TELEFONE_FOR": "4733334444", "CONTATO_FOR": "PAULO 99880-0000"},
    ])
    r = _importar(filial, banco, "02")
    assert (r.criados, r.ligados_por_documento, r.contatos) == (0, 1, 1)
    with banco() as db:
        tecidos = db.scalar(select(Fornecedor).where(Fornecedor.cpf_cnpj == CNPJ_A))
        assert tecidos.nome == "TECIDOS FICTICIOS LTDA"
        assert [c.nome for c in tecidos.contatos] == ["RITA", "PAULO"]
        assert len(tecidos.telefones) == 2
        assert mapa.buscar(db, "tab_fornecedores", empresas["02"], "9") == tecidos.id

    # reimportar não duplica; e a matriz, que manda, atualiza o nome
    with matriz.begin() as c:
        c.execute(text("UPDATE tab_fornecedores SET NOME_FOR = 'TECIDOS FICTICIOS S.A.' WHERE COD_FOR = 1"))
    r = _importar(matriz, banco, "01")
    assert (r.criados, r.atualizados, r.telefones, r.contatos) == (0, 2, 0, 0)
    with banco() as db:
        assert len(db.scalars(select(Fornecedor)).all()) == 2
        assert db.scalar(select(Fornecedor.nome).where(Fornecedor.cpf_cnpj == CNPJ_A)) == "TECIDOS FICTICIOS S.A."
    matriz.dispose()
    filial.dispose()


def test_descartado_depois_sai_do_banco_novo(banco, empresas, tmp_path):
    eng = _banco_vb6(tmp_path / "f01.db", [_TECIDOS])
    _importar(eng, banco, "01")
    with eng.begin() as c:
        c.execute(text("UPDATE tab_fornecedores SET CNPJ_FOR = '' WHERE COD_FOR = 1"))
    r = _importar(eng, banco, "01")
    eng.dispose()
    assert (r.descartados, r.excluidos) == (1, 1)
    with banco() as db:
        assert db.scalars(select(Fornecedor)).all() == []
        assert mapa.buscar(db, "tab_fornecedores", empresas["01"], "1") is None


def test_cidade_escrita_de_outro_jeito(banco, empresas, tmp_path):
    eng = _banco_vb6(tmp_path / "f01.db", [
        {**_TECIDOS, "CIDADE_FOR": "STA BARBARA DOESTE", "UF_FOR": "SP"},
        {**_TECIDOS, "COD_FOR": 2, "CNPJ_FOR": CNPJ_B, "CIDADE_FOR": "SAO BERNARDO DO CAMP", "UF_FOR": "SP"},
    ])
    r = _importar(eng, banco, "01")
    eng.dispose()
    assert not any("cidade" in a for a in r.avisos)
    with banco() as db:
        assert sorted(f.cidade.nome for f in db.scalars(select(Fornecedor))) == ["Santa Bárbara d'Oeste", "São Bernardo do Campo"]

