"""ETL de clientes. Dados fictícios (CPFs gerados só para teste): nada de dado real no repositório."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.acesso import servico
from app.dominios.clientes.modelos import Cliente, GrupoCliente, Orgao, Setor, SetorCobrador
from app.dominios.funcionarios.modelos import Funcionario
from etl import mapa
from etl.clientes import converter, importar_clientes
from etl.funcionarios import EmpresaNaoImportada

CPF_A = "52998224725"
CPF_B = "11144477735"


def _ddl(logradouro: str) -> list[str]:
    """Estrutura das tabelas do VB6. O nome da coluna do logradouro muda entre filiais."""
    return [
        f"""CREATE TABLE tab_clientes (
            cod_cli INTEGER PRIMARY KEY, nome_cli TEXT, datanasc_cli DATE, cpf_cli TEXT, endereco_cli TEXT,
            bairro_cli TEXT, cep_cli TEXT, referencia_cli TEXT, cidade_cli TEXT, uf_cli TEXT, data_cli DATE,
            obs_cli TEXT, status_cli TEXT, rg_cli TEXT, mae_cli TEXT, pai_cli TEXT, mens_cli TEXT,
            limite_cli REAL, endcom_cli TEXT, tipo_cli TEXT, cod_set TEXT, cod_gru TEXT, cobranca_cli TEXT,
            localtrab_cli TEXT, endtrab_cli TEXT, setortrab_cli TEXT, teltrab_cli TEXT, ceptrab_cli TEXT,
            cod_org TEXT, dataalt_cli DATE, sexo_cli TEXT, email_cli TEXT, creditosuspenso_cli TEXT, ie_cli TEXT,
            cod_cid TEXT, {logradouro} TEXT, numero_cli TEXT, complemento_cli TEXT, especial_cli TEXT)""",
        "CREATE TABLE tab_telefones (cod_cli INTEGER, num_tel TEXT, tipo_tel TEXT, tipo_ter TEXT)",
        """CREATE TABLE tab_referencias (cod_cli INTEGER, seq_ref INTEGER, nome_ref TEXT, cod_tip INTEGER,
            tel_ref TEXT, tipo_ref TEXT)""",
        """CREATE TABLE tab_clientesanot (id INTEGER PRIMARY KEY, cod_cli INTEGER, anotacao TEXT, datahora DATETIME,
            cod_usu TEXT, excluido TEXT)""",
        "CREATE TABLE tab_grupocli (cod_gru TEXT, nome_gru TEXT)",
        "CREATE TABLE tab_cidades (cod_cid TEXT, nome_cid TEXT, uf_cid TEXT, cod_mun TEXT)",
        "CREATE TABLE tab_setores (cod_set TEXT, nome_set TEXT, cobrador_set TEXT, cod_cid TEXT, cod_old TEXT, tipo_set TEXT)",
        """CREATE TABLE tab_orgaos (cod_org TEXT, nome_org TEXT, cod_gru TEXT, endereco_org TEXT, cod_set TEXT,
            fone_org TEXT, cep_org TEXT, cobrador_org TEXT, data_org DATE, Obs TEXT)""",
    ]


_ANA = {
    "cod_cli": 1, "nome_cli": "ANA FICTICIA", "datanasc_cli": "1985-02-30", "cpf_cli": "529.982.247-25",
    "endereco_cli": "RUA UM QD 1 LT 2", "bairro_cli": "CENTRO", "cep_cli": "75.000-000", "cidade_cli": "ANAPOLIS",
    "uf_cli": "go", "data_cli": "2010-01-01", "dataalt_cli": "2020-01-01", "status_cli": "1", "mens_cli": "S",
    "limite_cli": 550, "tipo_cli": "F", "cod_set": "00001", "cod_gru": "001", "cobranca_cli": "2",
    "cod_org": "00007", "sexo_cli": "F", "creditosuspenso_cli": "N", "cod_cid": "5201108", "especial_cli": "N",
}
_BETO = {**_ANA, "cod_cli": 2, "nome_cli": "BETO SEM CPF", "cpf_cli": "000.000.000-00", "cod_set": "00000",
         "cod_org": "", "sexo_cli": "M", "mens_cli": ""}


def _inserir(c, tabela: str, linha: dict) -> None:
    c.execute(text(f"INSERT INTO {tabela} ({', '.join(linha)}) VALUES ({', '.join(':' + k for k in linha)})"), linha)


def _banco_vb6(caminho, clientes, logradouro="Logradouro_cli", setores=(), orgaos=(), grupos=(),
               telefones=(), referencias=(), anotacoes=()):
    eng = create_engine(f"sqlite:///{caminho}")
    with eng.begin() as c:
        for ddl in _ddl(logradouro):
            c.execute(text(ddl))
        _inserir(c, "tab_cidades", {"cod_cid": "00001", "nome_cid": "ANAPOLIS", "uf_cid": "GO", "cod_mun": "5201108"})
        for linha in clientes:
            _inserir(c, "tab_clientes", linha)
        for cod, nome, cobrador in setores:
            _inserir(c, "tab_setores", {"cod_set": cod, "nome_set": nome, "cobrador_set": cobrador,
                                        "cod_cid": "00001", "tipo_set": "BAIRRO"})
        for cod, nome, grupo in orgaos:
            _inserir(c, "tab_orgaos", {"cod_org": cod, "nome_org": nome, "cod_gru": grupo, "endereco_org": "",
                                       "cod_set": "00001", "fone_org": "(62) 3333-0000", "cep_org": "", "Obs": None})
        for cod, nome in grupos:
            _inserir(c, "tab_grupocli", {"cod_gru": cod, "nome_gru": nome})
        for cod, num, tipo in telefones:
            _inserir(c, "tab_telefones", {"cod_cli": cod, "num_tel": num, "tipo_tel": tipo, "tipo_ter": "C"})
        for seq, (cod, nome, tel, tip) in enumerate(referencias):
            _inserir(c, "tab_referencias", {"cod_cli": cod, "seq_ref": seq, "nome_ref": nome, "cod_tip": tip,
                                            "tel_ref": tel, "tipo_ref": ""})
        for id_, cod, texto, excluido in anotacoes:
            _inserir(c, "tab_clientesanot", {"id": id_, "cod_cli": cod, "anotacao": texto,
                                             "datahora": "2021-10-27 15:49:46", "cod_usu": "058", "excluido": excluido})
    return eng


@pytest.fixture
def empresas(banco):
    with banco() as db:
        e1 = servico.criar_empresa(db, "01", "MATRIZ")
        e3 = servico.criar_empresa(db, "03", "FILIAL")
        # o cobrador 003 da matriz, como o ETL de funcionários deixaria
        f = Funcionario(nome="COBRADOR FICTICIO", empresa_id=e1.id)
        db.add(f)
        db.flush()
        mapa.gravar(db, "tab_funcionarios", e1.id, "003", f.id)
        db.commit()
        return {"01": e1.id, "03": e3.id, "cobrador": f.id}


@pytest.fixture
def matriz(tmp_path):
    eng = _banco_vb6(
        tmp_path / "f01.db", [_ANA, _BETO],
        setores=[("00001", "JUNDIAÍ", "003"), ("00002", "CENTRO", "099")],
        orgaos=[("00007", "ESCOLA MODELO", "001")],
        grupos=[("000", "GERAL"), ("001", "SERVIDOR MUNICIPAL")],
        telefones=[(1, "(62) 99999-0000", "3"), (1, "3333-4444", "1"), (2, "62 98888-7777", "3")],
        referencias=[(1, "LOJA VIZINHA", "3311-0000", 1)],
        anotacoes=[(10, 1, "PAGA EM DIA", "N"), (11, 1, "APAGADA", "S")],
    )
    yield eng
    eng.dispose()


def _importar(eng, banco, codigo):
    with eng.connect() as c, banco() as db:
        return importar_clientes(c, db, codigo)


def test_converter():
    d = converter(_ANA)
    assert d["uf"] == "GO"
    assert d["cep"] == "75000000"
    assert d["data_nascimento"] is None  # 30 de fevereiro
    assert d["limite_credito"] == Decimal("550.00")
    assert d["forma_cobranca"] == "2"
    assert d["recebe_mensagens"] is True
    assert d["codigo_municipio"] == "5201108"
    assert d["logradouro"] == "RUA UM QD 1 LT 2"


def test_empresa_precisa_existir(banco, matriz):
    with pytest.raises(EmpresaNaoImportada):
        _importar(matriz, banco, "01")


def test_importa_matriz(banco, empresas, matriz):
    r = _importar(matriz, banco, "01")
    assert (r.grupos_criados, r.setores_criados, r.orgaos_criados, r.cobradores) == (2, 2, 1, 1)
    assert (r.criados, r.sem_documento, r.telefones, r.referencias, r.anotacoes) == (2, 1, 3, 1, 1)
    assert any("cobrador 099" in a for a in r.avisos)
    assert not any("BETO" in a for a in r.avisos)  # CPF só de zeros é "sem CPF", não aviso

    with banco() as db:
        ana = db.scalar(select(Cliente).where(Cliente.cpf_cnpj == CPF_A))
        assert ana.nome == "ANA FICTICIA"
        assert ana.data_cadastro == date(2010, 1, 1)
        assert ana.data_alteracao == date(2020, 1, 1)
        assert ana.empresa_cadastro_id == empresas["01"]
        assert ana.setor.nome == "JUNDIAÍ" and ana.setor.cidade == "ANAPOLIS"
        assert ana.orgao.nome == "ESCOLA MODELO" and ana.orgao.grupo.nome == "SERVIDOR MUNICIPAL"
        assert ana.grupo.nome == "SERVIDOR MUNICIPAL"
        assert {t.numero for t in ana.telefones} == {"62999990000", "33334444"}
        assert [(ref.nome, ref.telefone, ref.tipo) for ref in ana.referencias] == [("LOJA VIZINHA", "33110000", "1")]
        assert [a.texto for a in ana.anotacoes] == ["PAGA EM DIA"]
        beto = db.scalar(select(Cliente).where(Cliente.nome == "BETO SEM CPF"))
        assert beto.cpf_cnpj is None and beto.setor is None and beto.recebe_mensagens is False
        cobrador = db.scalar(select(SetorCobrador))
        assert (cobrador.empresa_id, cobrador.funcionario_id) == (empresas["01"], empresas["cobrador"])


def test_reimportar_nao_duplica(banco, empresas, matriz):
    _importar(matriz, banco, "01")
    r = _importar(matriz, banco, "01")
    assert (r.criados, r.atualizados, r.grupos_criados, r.setores_criados, r.orgaos_criados) == (0, 2, 0, 0, 0)
    assert (r.telefones, r.referencias, r.anotacoes) == (0, 0, 0)
    with banco() as db:
        assert len(db.scalars(select(Cliente)).all()) == 2


def test_outra_loja_junta_pelo_cpf_e_o_mais_recente_manda(banco, empresas, matriz, tmp_path):
    _importar(matriz, banco, "01")
    # na filial, a ANA foi alterada depois (mudou de endereço) e o código 1 é de outra pessoa
    filial = _banco_vb6(
        tmp_path / "f03.db",
        [
            {**_ANA, "cod_cli": 7, "nome_cli": "ANA FICTICIA SILVA", "endereco_cli": "", "logradouro_cli": "RUA DOIS",
             "data_cli": "2008-05-05", "dataalt_cli": "2023-03-03", "cod_set": "00009", "cod_org": "", "pai_cli": "PAI"},
            {**_ANA, "cod_cli": 1, "nome_cli": "CARLA FICTICIA", "cpf_cli": CPF_B, "cod_set": "00001",
             "dataalt_cli": "2015-01-01", "cod_org": ""},
            {**_BETO, "cod_cli": 2},
        ],
        logradouro="logradouro_cli",
        setores=[("00009", "jundiai", ""), ("00001", "VILA NOVA", "")],
        grupos=[("001", "Servidor Municipal")],
        telefones=[(7, "62 99999-0000", "3"), (7, "62 97777-1111", "3")],
    )
    r = _importar(filial, banco, "03")
    filial.dispose()
    assert (r.criados, r.ligados_por_documento, r.sem_documento) == (2, 1, 1)
    assert (r.setores_criados, r.grupos_criados) == (1, 0)  # "jundiai" é o mesmo setor "JUNDIAÍ"
    assert r.telefones == 1  # o 62 99999-0000 já existia na ANA

    with banco() as db:
        ana = db.scalar(select(Cliente).where(Cliente.cpf_cnpj == CPF_A))
        assert ana.nome == "ANA FICTICIA SILVA"
        assert ana.logradouro == "RUA DOIS"
        assert ana.pai == "PAI"
        assert ana.data_alteracao == date(2023, 3, 3)
        assert ana.setor.nome == "JUNDIAÍ"
        assert ana.orgao.nome == "ESCOLA MODELO"  # vazio na filial: fica o da matriz
        # a filial tem o cadastro mais antigo
        assert ana.data_cadastro == date(2008, 5, 5) and ana.empresa_cadastro_id == empresas["03"]
        assert len(ana.telefones) == 3

        carla = db.scalar(select(Cliente).where(Cliente.cpf_cnpj == CPF_B))
        assert carla.setor.nome == "VILA NOVA"  # o código 00001 da filial não é o 00001 da matriz
        # sem CPF, o BETO da filial não é juntado ao da matriz
        assert len(db.scalars(select(Cliente).where(Cliente.nome == "BETO SEM CPF")).all()) == 2
        assert len(db.scalars(select(Setor)).all()) == 3
        assert len(db.scalars(select(GrupoCliente)).all()) == 2
        assert len(db.scalars(select(Orgao)).all()) == 1

    # a matriz, reimportada com dado mais antigo, não desfaz a alteração da filial
    _importar(matriz, banco, "01")
    with banco() as db:
        ana = db.scalar(select(Cliente).where(Cliente.cpf_cnpj == CPF_A))
        assert ana.nome == "ANA FICTICIA SILVA"
        assert ana.data_alteracao == date(2023, 3, 3)
