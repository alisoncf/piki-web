"""ETL de empresas. Dados fictícios: nada de dado real no repositório."""
import pytest
from sqlalchemy import create_engine, inspect, select, text

from app.dominios.cidades.modelos import Cidade
from app.dominios.empresas.modelos import Empresa
from etl.empresas import ConflitoEmpresa, converter, importar_empresas

# estrutura da sped_empresa no VB6, com as colunas sensíveis
_DDL = """
CREATE TABLE sped_empresa (
  codigo TEXT PRIMARY KEY, cnpj TEXT, apelido TEXT, cpf TEXT, UF TEXT, IE TEXT, nome TEXT,
  cod_mun TEXT, im TEXT, suframa TEXT, ind_perfil TEXT, ind_atv TEXT, fantasia TEXT, cep TEXT,
  endereco TEXT, numero TEXT, complemento TEXT, bairro TEXT, fone TEXT, fax TEXT, email TEXT,
  caminho_certificado TEXT, senha_certificado TEXT, idcsc TEXT, token TEXT, caminho_logo TEXT,
  caminho_qrcodedoc TEXT, cor TEXT, crt TEXT
)
"""

_LOJA_A = {
    "codigo": "01", "cnpj": "11.222.333/0001-81", "apelido": "MATRIZ", "UF": "go", "IE": "10.111.222-3",
    "nome": "EMPRESA FICTICIA LTDA", "cod_mun": "5201108", "im": "", "ind_perfil": "1", "ind_atv": "1",
    "fantasia": "LOJA FICTICIA", "cep": "75000-000", "endereco": "RUA DE TESTE", "numero": "100",
    "complemento": "", "bairro": "CENTRO", "fone": "62 3333-4444", "email": "LOJA@EXEMPLO.COM",
    "caminho_certificado": "C:\\cert\\teste.pfx", "senha_certificado": "senha-fake", "idcsc": "1",
    "token": "token-fake", "crt": "1",
}
_LOJA_B = {**_LOJA_A, "codigo": "03", "cnpj": "44555666000110", "apelido": "FILIAL", "nome": "OUTRA FICTICIA LTDA"}


@pytest.fixture
def origem(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'vb6.db'}")
    with eng.begin() as c:
        c.execute(text(_DDL))
        for loja in (_LOJA_A, _LOJA_B):
            c.execute(text(f"INSERT INTO sped_empresa ({', '.join(loja)}) VALUES ({', '.join(':' + k for k in loja)})"), loja)
    yield eng
    eng.dispose()


def test_converter_normaliza():
    d = converter(_LOJA_A)
    assert d["cnpj"] == "11222333000181"
    assert d["inscricao_estadual"] == "101112223"
    assert d["cep"] == "75000000"
    assert d["telefone"] == "6233334444"
    assert d["codigo_ibge"] == "5201108"
    assert d["email"] == "loja@exemplo.com"
    assert d["nome"] == "MATRIZ"
    assert d["inscricao_municipal"] is None  # texto vazio vira nulo
    # códigos fiscais: o ind_perfil '1' das lojas não é perfil do SPED (A, B ou C)
    assert (d["crt"], d["sped_perfil"], d["sped_atividade"]) == ("1", None, "1")
    assert converter({**_LOJA_A, "ind_perfil": "b", "crt": "9"})["sped_perfil"] == "B"
    assert converter({**_LOJA_A, "crt": "9"})["crt"] is None


def test_segredos_nao_sao_lidos():
    # nem a consulta nem o modelo conhecem as colunas sensíveis
    from etl.empresas import _CONSULTA

    sql = str(_CONSULTA).lower()
    for coluna in ("senha_certificado", "caminho_certificado", "token", "idcsc"):
        assert coluna not in sql
    colunas = {c.key for c in inspect(Empresa).columns}
    assert not colunas & {"senha_certificado", "token", "idcsc", "caminho_certificado"}


def test_importa_e_e_repetivel(origem, banco):
    with origem.connect() as c, banco() as db:
        db.add(Cidade(codigo_ibge="5201108", nome="Anápolis", uf="GO", nome_busca="anapolis"))
        db.commit()
        r1 = importar_empresas(c, db)
        r2 = importar_empresas(c, db)
        assert r1.criadas == ["01", "03"] and r1.atualizadas == []
        assert r2.criadas == [] and r2.atualizadas == ["01", "03"]
        empresas = db.scalars(select(Empresa).order_by(Empresa.codigo)).all()
        assert [(e.codigo, e.nome, e.cnpj) for e in empresas] == [
            ("01", "MATRIZ", "11222333000181"),
            ("03", "FILIAL", "44555666000110"),
        ]
        assert empresas[0].cidade.nome == "Anápolis"


def test_atualiza_dados_alterados(origem, banco):
    with origem.connect() as c, banco() as db:
        importar_empresas(c, db)
        c.execute(text("UPDATE sped_empresa SET bairro = 'NOVO BAIRRO' WHERE codigo = '01'"))
        importar_empresas(c, db)
        assert db.scalar(select(Empresa.bairro).where(Empresa.codigo == "01")) == "NOVO BAIRRO"


def test_conflito_de_cnpj(origem, banco):
    with origem.connect() as c, banco() as db:
        importar_empresas(c, db)
        c.execute(text("UPDATE sped_empresa SET cnpj = '99888777000166' WHERE codigo = '03'"))
        with pytest.raises(ConflitoEmpresa, match="Empresa 03"):
            importar_empresas(c, db)
