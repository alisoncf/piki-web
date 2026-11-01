"""ETL de clientes. Dados fictícios (CPFs gerados só para teste): nada de dado real no repositório."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.clientes.modelos import AnotacaoCliente, Cliente, GrupoCliente, Orgao, Setor
from app.dominios.empresas.esquemas import EmpresaNova
from app.dominios.empresas.servico import criar_empresa
from app.dominios.funcionarios.modelos import Funcionario
from etl import mapa
from etl.clientes import converter, corrigir_nome, importar_clientes, nome_sem_sentido
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
            cod_cid TEXT, {logradouro} TEXT, numero_cli TEXT, complemento_cli TEXT, especial_cli TEXT,
            logradouro TEXT, numero TEXT, complemento TEXT)""",
        "CREATE TABLE tab_telefones (cod_cli INTEGER, num_tel TEXT, tipo_tel TEXT, tipo_ter TEXT)",
        """CREATE TABLE tab_referencias (cod_cli INTEGER, seq_ref INTEGER, nome_ref TEXT, cod_tip INTEGER,
            tel_ref TEXT, tipo_ref TEXT)""",
        """CREATE TABLE tab_clientesanot (id INTEGER PRIMARY KEY, cod_cli INTEGER, anotacao TEXT, datahora DATETIME,
            cod_usu TEXT, excluido TEXT)""",
        "CREATE TABLE tab_grupocli (cod_gru TEXT, nome_gru TEXT)",
        "CREATE TABLE tab_tipopar (cod_tip INTEGER PRIMARY KEY, nome_tip TEXT)",
        "CREATE TABLE tab_cidades (cod_cid TEXT, nome_cid TEXT, uf_cid TEXT, cod_mun TEXT)",
        "CREATE TABLE tab_funcionarios (cod_fun TEXT, cod_set TEXT)",
        "CREATE TABLE tab_setores (cod_set TEXT, nome_set TEXT, cobrador_set TEXT, cod_cid TEXT, cod_old TEXT, tipo_set TEXT)",
        """CREATE TABLE tab_orgaos (cod_org TEXT, nome_org TEXT, cod_gru TEXT, endereco_org TEXT, cod_set TEXT,
            fone_org TEXT, cep_org TEXT, cobrador_org TEXT, data_org DATE, Obs TEXT)""",
        "CREATE TABLE tab_doc (seq_doc INTEGER PRIMARY KEY, cod_ter TEXT, tipo_ter TEXT, excluido_doc TEXT)",
        "CREATE TABLE tab_itdoc (seq_itd INTEGER PRIMARY KEY, seq_doc INTEGER, reman_itd REAL)",
    ]


_ANA = {
    "cod_cli": 1, "nome_cli": "ANA FICTICIA", "datanasc_cli": "1985-02-30", "cpf_cli": "529.982.247-25",
    "endereco_cli": "R UM", "logradouro": "RUA UM QD 1 LT 2", "numero": "10", "bairro_cli": "CENTRO", "cep_cli": "75.000-000", "cidade_cli": "ANAPOLIS",
    "uf_cli": "go", "data_cli": "2010-01-01", "dataalt_cli": "2020-01-01", "status_cli": "1", "mens_cli": "S",
    "limite_cli": 550, "tipo_cli": "F", "cod_set": "00001", "cod_gru": "001", "cobranca_cli": "2",
    "cod_org": "00007", "sexo_cli": "F", "creditosuspenso_cli": "N", "cod_cid": "5201108", "especial_cli": "N",
}
_BETO = {**_ANA, "cod_cli": 2, "nome_cli": "BETO SEM CPF", "cpf_cli": "000.000.000-00", "cod_set": "00000",
         "status_cli": "2", "cobranca_cli": "3",
         "cod_org": "", "sexo_cli": "M", "mens_cli": ""}


def _inserir(c, tabela: str, linha: dict) -> None:
    c.execute(text(f"INSERT INTO {tabela} ({', '.join(linha)}) VALUES ({', '.join(':' + k for k in linha)})"), linha)


def _banco_vb6(caminho, clientes, logradouro="Logradouro_cli", setores=(), orgaos=(), grupos=(),
               telefones=(), referencias=(), anotacoes=(), dividas=()):
    eng = create_engine(f"sqlite:///{caminho}")
    with eng.begin() as c:
        for ddl in _ddl(logradouro):
            c.execute(text(ddl))
        for cod, nome in ((0, "Outro"), (1, "Cônjuge"), (3, "Pais")):
            _inserir(c, "tab_tipopar", {"cod_tip": cod, "nome_tip": nome})
        # o cobrador SIDNEI mora no setor 00001 (códigos 003 na matriz e 010 na filial, ver a fixture empresas)
        for cod in ("003", "010"):
            _inserir(c, "tab_funcionarios", {"cod_fun": cod, "cod_set": "00001"})
        # com o código do IBGE; sem ele, mas com o nome certo; e uma que não é cidade (bairro digitado como cidade)
        for cod, nome, mun in (("00001", "ANAPOLIS", "5201108"), ("00002", "GOIANIA", ""), ("00003", "JUNDIAI", ""),
                               ("00004", "CORUMBA", "")):
            _inserir(c, "tab_cidades", {"cod_cid": cod, "nome_cid": nome, "uf_cid": "GO", "cod_mun": mun})
        for linha in clientes:
            _inserir(c, "tab_clientes", linha)
        for cod, nome, cobrador, *cidade in setores:
            _inserir(c, "tab_setores", {"cod_set": cod, "nome_set": nome, "cobrador_set": cobrador,
                                        "cod_cid": cidade[0] if cidade else "00001", "tipo_set": "BAIRRO"})
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
        # dividas: (cod_cli, saldo da parcela); saldo zero é parcela paga
        for seq, (cod, saldo) in enumerate(dividas, start=1):
            _inserir(c, "tab_doc", {"seq_doc": seq, "cod_ter": f"{cod:06d}", "tipo_ter": "C", "excluido_doc": "N"})
            _inserir(c, "tab_itdoc", {"seq_itd": seq, "seq_doc": seq, "reman_itd": saldo})
    return eng


@pytest.fixture
def empresas(banco):
    with banco() as db:
        e1 = criar_empresa(db, EmpresaNova(codigo="01", nome="MATRIZ"))
        e3 = criar_empresa(db, EmpresaNova(codigo="03", nome="FILIAL"))
        # parte da lista do IBGE, que no banco de verdade vem da migração
        db.add_all([Cidade(codigo_ibge=c, nome=n, uf="GO", nome_busca=nome_de_busca(n))
                    for c, n in (("5201108", "Anápolis"), ("5208707", "Goiânia"), ("5205901", "Corumbá de Goiás"),
                                 ("5201405", "Aparecida de Goiânia"))])
        # o cobrador, como o ETL de funcionários deixaria: um cadastro só, com um código em cada loja
        sidnei = Funcionario(nome="SIDNEI", empresa_id=e1.id)
        db.add(sidnei)
        db.flush()
        mapa.gravar(db, "tab_funcionarios", e1.id, "003", sidnei.id)
        mapa.gravar(db, "tab_funcionarios", e3.id, "010", sidnei.id)
        db.commit()
        return {"01": e1.id, "03": e3.id}


@pytest.fixture
def matriz(tmp_path):
    eng = _banco_vb6(
        tmp_path / "f01.db", [_ANA, _BETO],
        setores=[("00001", "JUNDIAÍ", "003"), ("00002", "CENTRO", "099", "00002"), ("00003", "SAO JOAO", "003", "00003"),
                 ("00004", "VILA SANTA", "", "00004")],
        orgaos=[("00007", "ESCOLA MODELO", "001")],
        grupos=[("000", "GERAL"), ("001", "SERVIDOR MUNICIPAL")],
        telefones=[(1, "(62) 99999-0000", "3"), (1, "3333-4444", "1"), (2, "62 98888-7777", "3")],
        referencias=[(1, "LOJA VIZINHA", "3311-0000", 1)],
        anotacoes=[(10, 1, "PAGA EM DIA", "N"), (11, 1, "APAGADA", "S")],
        dividas=[(2, 80.0)],  # o BETO, sem CPF, ainda deve: fica (D21)
    )
    yield eng
    eng.dispose()


def _importar(eng, banco, codigo):
    with eng.connect() as c, banco() as db:
        return importar_clientes(c, db, codigo)


def test_converter():
    d = converter(_ANA)
    assert d["cep"] == "75000000"
    assert d["data_nascimento"] is None  # 30 de fevereiro
    assert d["limite_credito"] == Decimal("550.00")
    assert d["forma_cobranca"] == "trabalho"
    assert d["bloqueado"] is False
    assert converter(_BETO)["bloqueado"] is True
    assert converter(_BETO)["forma_cobranca"] == "loja"
    assert d["recebe_mensagens"] is True
    assert "cidade" not in d and "uf" not in d  # a cidade é a do setor
    # o logradouro manda; endereco_cli só quando os outros estão vazios
    assert (d["logradouro"], d["numero"]) == ("RUA UM QD 1 LT 2", "10")
    assert converter({**_ANA, "logradouro": ""})["logradouro"] == "R UM"


def test_empresa_precisa_existir(banco, matriz):
    with pytest.raises(EmpresaNaoImportada):
        _importar(matriz, banco, "01")


def test_importa_matriz(banco, empresas, matriz):
    r = _importar(matriz, banco, "01")
    assert (r.grupos_criados, r.parentescos_criados, r.setores_criados, r.orgaos_criados) == (2, 3, 4, 1)
    assert (r.cobradores, r.setores_sem_cidade, r.funcionarios_no_setor) == (2, 1, 1)
    assert (r.criados, r.sem_documento, r.telefones, r.referencias, r.anotacoes) == (2, 1, 3, 1, 1)
    assert any("cobrador 099" in a for a in r.avisos)
    assert any("cidade 00003 (JUNDIAI/GO)" in a for a in r.avisos)
    assert (r.mantidos_por_divida, r.descartados) == (1, 0)
    assert any("BETO SEM CPF): sem CPF/CNPJ válido, mantido por ter parcela em aberto" in a for a in r.avisos)

    with banco() as db:
        ana = db.scalar(select(Cliente).where(Cliente.cpf_cnpj == CPF_A))
        assert ana.nome == "ANA FICTICIA"
        assert ana.data_cadastro == date(2010, 1, 1)
        assert ana.data_alteracao == date(2020, 1, 1)
        assert ana.empresa_cadastro_id == empresas["01"]
        assert ana.setor.nome == "JUNDIAÍ" and ana.setor.cidade.nome == "Anápolis"
        assert ana.orgao.nome == "ESCOLA MODELO" and ana.orgao.grupo.nome == "SERVIDOR MUNICIPAL"
        assert ana.grupo.nome == "SERVIDOR MUNICIPAL"
        assert {t.numero for t in ana.telefones} == {"62999990000", "33334444"}
        assert [(ref.nome, ref.telefone, ref.parentesco.nome) for ref in ana.referencias] == [
            ("LOJA VIZINHA", "33110000", "Cônjuge")]
        assert [a.texto for a in ana.anotacoes] == ["PAGA EM DIA"]
        beto = db.scalar(select(Cliente).where(Cliente.nome == "BETO SEM CPF"))
        assert beto.cpf_cnpj is None and beto.setor is None and beto.recebe_mensagens is False
        assert beto.bloqueado is True and beto.forma_cobranca == "loja"
        setores = {s.nome: s for s in db.scalars(select(Setor))}
        assert setores["CENTRO"].cidade.nome == "Goiânia"  # achada pelo nome
        assert setores["VILA SANTA"].cidade.nome == "Corumbá de Goiás"  # pelo começo do nome
        assert setores["SAO JOAO"].cidade is None
        assert [c.nome for c in setores["SAO JOAO"].cobradores] == ["SIDNEI"]
        assert setores["SAO JOAO"].cobradores[0].setor.nome == "JUNDIAÍ"  # o setor onde ele mora


def test_reimportar_nao_duplica(banco, empresas, matriz):
    _importar(matriz, banco, "01")
    r = _importar(matriz, banco, "01")
    assert (r.criados, r.atualizados, r.grupos_criados, r.parentescos_criados, r.setores_criados, r.orgaos_criados) == (
        0, 2, 0, 0, 0, 0)
    assert (r.telefones, r.referencias, r.anotacoes) == (0, 0, 0)
    with banco() as db:
        assert len(db.scalars(select(Cliente)).all()) == 2


def test_outra_loja_junta_pelo_cpf_e_o_mais_recente_manda(banco, empresas, matriz, tmp_path):
    _importar(matriz, banco, "01")
    # na filial, a ANA foi alterada depois (mudou de endereço) e o código 1 é de outra pessoa
    filial = _banco_vb6(
        tmp_path / "f03.db",
        [
            {**_ANA, "cod_cli": 7, "nome_cli": "ANA FICTICIA SILVA", "logradouro": "", "logradouro_cli": "RUA DOIS",
             "data_cli": "2008-05-05", "dataalt_cli": "2023-03-03", "cod_set": "00009", "cod_org": "", "pai_cli": "PAI"},
            {**_ANA, "cod_cli": 1, "nome_cli": "CARLA FICTICIA", "cpf_cli": CPF_B, "cod_set": "00001",
             "dataalt_cli": "2015-01-01", "cod_org": ""},
            {**_BETO, "cod_cli": 2},
        ],
        logradouro="logradouro_cli",
        setores=[("00009", "jundiai", "010"), ("00001", "VILA NOVA", "010")],
        grupos=[("001", "Servidor Municipal")],
        telefones=[(7, "62 99999-0000", "3"), (7, "62 97777-1111", "3")],
    )
    r = _importar(filial, banco, "03")
    filial.dispose()
    assert (r.criados, r.ligados_por_documento, r.sem_documento, r.descartados) == (1, 1, 0, 1)
    assert (r.setores_criados, r.grupos_criados) == (1, 0)  # "jundiai" é o mesmo setor "JUNDIAÍ"
    assert r.cobradores == 1  # o mesmo SIDNEI, que já cobrava o JUNDIAÍ
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
        # sem CPF e sem dívida, o BETO da filial não entra; o da matriz (que deve) fica
        assert len(db.scalars(select(Cliente).where(Cliente.nome == "BETO SEM CPF")).all()) == 1
        assert len(db.scalars(select(Setor)).all()) == 5
        # um cobrador para todas as lojas, em vários setores
        sidnei = db.scalar(select(Funcionario).where(Funcionario.nome == "SIDNEI"))
        # na filial ele mora no 00001 (VILA NOVA), mas manda a loja onde está lotado
        assert sidnei.setor.nome == "JUNDIAÍ"
        assert sorted(s.nome for s in db.scalars(select(Setor)) if sidnei in s.cobradores) == [
            "JUNDIAÍ", "SAO JOAO", "VILA NOVA"]
        assert len(db.scalars(select(GrupoCliente)).all()) == 2
        assert len(db.scalars(select(Orgao)).all()) == 1

    # a matriz, reimportada com dado mais antigo, não desfaz a alteração da filial
    _importar(matriz, banco, "01")
    with banco() as db:
        ana = db.scalar(select(Cliente).where(Cliente.cpf_cnpj == CPF_A))
        assert ana.nome == "ANA FICTICIA SILVA"
        assert ana.data_alteracao == date(2023, 3, 3)


def test_nomes_corrigidos_e_sem_sentido():
    assert corrigir_nome("JOANA FICTICIA D0S SANTOS") == "JOANA FICTICIA DOS SANTOS"
    assert corrigir_nome("PAUL0 FICTICIO") == "PAULO FICTICIO"
    assert corrigir_nome("ANA FICTICIA N.470") == "ANA FICTICIA"
    assert corrigir_nome("BIA FICTICIA N 160 ") == "BIA FICTICIA"
    assert corrigir_nome("CARLA FICTICIA 12345678900") == "CARLA FICTICIA"
    assert corrigir_nome("LOJA 011 FICTICIA LTDA") == "LOJA 011 FICTICIA LTDA"  # número no meio fica
    assert corrigir_nome("DORA FICTICIA  Q 3 L 2") == "DORA FICTICIA"
    assert corrigir_nome("EDU FICTICIO R06 N142") == "EDU FICTICIO"
    assert corrigir_nome("MARIA FICTICIA PRAD0") == "MARIA FICTICIA PRADO"
    assert corrigir_nome("MARIA C") == "MARIA C"  # inicial do sobrenome, não endereço
    for nome in ("TESTE", "teste loja", "+", "5", "214564156", "RUA DAS FLORES Q 1 L 2 CASA", None, ""):
        assert nome_sem_sentido(corrigir_nome(nome)), nome
    for nome in ("JOANA", "ANA FICTICIA", "FICTICIA E CIA LTDA", "RUANA FICTICIA"):
        assert not nome_sem_sentido(nome), nome


def test_descartados_saem_do_banco_novo(banco, empresas, tmp_path):
    """Sem CPF válido ou com nome sem sentido, e sem dívida em aberto: não entra, e sai se já tinha entrado."""
    linhas = [
        {**_ANA, "cod_cli": 1, "nome_cli": "ANA D0S SANTOS N.10"},
        {**_BETO, "cod_cli": 2},  # sem CPF, sem dívida
        {**_BETO, "cod_cli": 3, "nome_cli": "CARLA SEM CPF"},  # sem CPF, deve
        {**_ANA, "cod_cli": 4, "nome_cli": "TESTE", "cpf_cli": CPF_B},  # CPF válido, nome sem sentido
        {**_BETO, "cod_cli": 5, "nome_cli": "DORA SEM CPF"},  # sem CPF, parcela já paga
    ]
    eng = _banco_vb6(tmp_path / "f01.db", linhas, dividas=[(3, 50.0), (5, 0.0)],
                     anotacoes=[(20, 2, "LIGAR DEPOIS", "N")])
    r = _importar(eng, banco, "01")
    assert (r.criados, r.descartados, r.mantidos_por_divida, r.excluidos, r.nomes_corrigidos) == (2, 3, 1, 0, 1)
    with banco() as db:
        assert sorted(c.nome for c in db.scalars(select(Cliente))) == ["ANA DOS SANTOS", "CARLA SEM CPF"]

    # cadastros importados antes da regra (aqui, gravados à mão) são excluídos na próxima importação
    with banco() as db:
        beto = Cliente(nome="BETO SEM CPF", data_cadastro=date(2010, 1, 1), empresa_cadastro_id=empresas["01"])
        beto.anotacoes.append(AnotacaoCliente(texto="LIGAR DEPOIS"))
        teste = Cliente(nome="TESTE", cpf_cnpj=CPF_B, data_cadastro=date(2010, 1, 1))
        dora = Cliente(nome="DORA SEM CPF", data_cadastro=date(2010, 1, 1))
        db.add_all([beto, teste, dora])
        db.flush()
        for cod, cliente in (("2", beto), ("4", teste), ("5", dora)):
            mapa.gravar(db, "tab_clientes", empresas["01"], cod, cliente.id)
        mapa.gravar(db, "tab_clientesanot", empresas["01"], "20", beto.anotacoes[0].id)
        # a DORA também veio de outra loja: fica, só perde a ligação com esta
        mapa.gravar(db, "tab_clientes", empresas["03"], "9", dora.id)
        db.commit()
    r = _importar(eng, banco, "01")
    eng.dispose()
    assert (r.descartados, r.excluidos) == (3, 2)
    with banco() as db:
        assert sorted(c.nome for c in db.scalars(select(Cliente))) == ["ANA DOS SANTOS", "CARLA SEM CPF", "DORA SEM CPF"]
        assert mapa.buscar(db, "tab_clientes", empresas["01"], "5") is None
        assert mapa.buscar(db, "tab_clientesanot", empresas["01"], "20") is None

