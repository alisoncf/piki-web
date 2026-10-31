"""ETL de funcionários. Dados fictícios: nada de dado real no repositório."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.acesso import servico
from app.dominios.funcionarios.modelos import Cargo, Funcionario
from etl.funcionarios import EmpresaNaoImportada, converter, importar_funcionarios

# estrutura das tabelas do VB6 (só as colunas lidas e algumas a mais)
_DDL = [
    "CREATE TABLE tab_cargos (COD_CAR TEXT PRIMARY KEY, NOME_CAR TEXT, venda_Car TEXT, cobranca_car TEXT)",
    """CREATE TABLE tab_funcionarios (
        cod_fun TEXT PRIMARY KEY, nome_fun TEXT, endereco_fun TEXT, bairro_fun TEXT, cidade_fun TEXT, uf_fun TEXT,
        cep_fun TEXT, nasc_fun TEXT, natural_fun TEXT, rg_fun TEXT, cpf_fun TEXT, sexo_fun TEXT, conjuge_fun TEXT,
        pai_fun TEXT, mae_fun TEXT, endpais_fun TEXT, datacad_fun TEXT, obs_fun TEXT, status_rep TEXT, cod_old TEXT,
        status_fun TEXT, cod_Car TEXT, guerra_fun TEXT, limite_fun REAL, cod_set TEXT, vale_fun TEXT)""",
    "CREATE TABLE tab_telefones (cod_cli INTEGER, num_tel TEXT, tipo_tel TEXT, tipo_ter TEXT)",
]

_ANA = {
    "cod_fun": "001", "nome_fun": "ANA FICTICIA", "guerra_fun": "ANINHA", "endereco_fun": "RUA TESTE 1",
    "bairro_fun": "CENTRO", "cidade_fun": "ANAPOLIS", "uf_fun": "go", "cep_fun": "75000-000",
    "nasc_fun": "1990-05-12", "natural_fun": "GOIANIA", "rg_fun": "123", "cpf_fun": "529.982.247-25",
    "sexo_fun": "f", "datacad_fun": "2015-03-01", "obs_fun": "", "status_fun": "1", "cod_car": "001",
    "limite_fun": 150.5, "vale_fun": "S",
}
_BRUNO = {**_ANA, "cod_fun": "002", "nome_fun": "BRUNO FICTICIO", "guerra_fun": "BRUNO", "cpf_fun": "123",
          "nasc_fun": "0000-00-00", "sexo_fun": "", "status_fun": "0", "cod_car": "002", "vale_fun": "N"}


def _banco_vb6(caminho, funcionarios, cargos, telefones=()):
    eng = create_engine(f"sqlite:///{caminho}")
    with eng.begin() as c:
        for ddl in _DDL:
            c.execute(text(ddl))
        for cod, nome, vende in cargos:
            c.execute(text("INSERT INTO tab_cargos VALUES (:c, :n, :v, 'N')"), {"c": cod, "n": nome, "v": vende})
        for f in funcionarios:
            c.execute(text(f"INSERT INTO tab_funcionarios ({', '.join(f)}) VALUES ({', '.join(':' + k for k in f)})"), f)
        for cod, num, tipo, ter in telefones:
            c.execute(text("INSERT INTO tab_telefones VALUES (:c, :n, :t, :r)"), {"c": cod, "n": num, "t": tipo, "r": ter})
    return eng


@pytest.fixture
def empresas(banco):
    with banco() as db:
        e1 = servico.criar_empresa(db, "01", "MATRIZ")
        e3 = servico.criar_empresa(db, "03", "FILIAL")
        return {"01": e1.id, "03": e3.id}


@pytest.fixture
def matriz(tmp_path):
    eng = _banco_vb6(
        tmp_path / "f01.db",
        [_ANA, _BRUNO],
        [("001", "VENDEDOR", "S"), ("002", "CAIXA", "N")],
        # cod_cli é numérico no VB6 (int zerofill): 1 = funcionário 001
        [(1, "(62) 99999-0000", "3", "U"), (1, "3333-4444", "1", "U"), (1, "62 98888-7777", "3", "C")],
    )
    yield eng
    eng.dispose()


def _importar(eng, banco, codigo):
    with eng.connect() as c, banco() as db:
        return importar_funcionarios(c, db, codigo)


def test_converter():
    d = converter(_ANA)
    assert "cidade" not in d and "bairro" not in d  # vêm do setor, ligado pelo ETL de clientes
    assert d["sexo"] == "F"
    assert d["cep"] == "75000000"
    assert d["data_nascimento"] == date(1990, 5, 12)
    assert d["limite_vale"] == Decimal("150.50")
    assert d["ativo"] is True
    assert d["observacao"] is None
    b = converter(_BRUNO)
    assert b["data_nascimento"] is None
    assert b["sexo"] is None
    assert b["ativo"] is False
    assert b["pode_tirar_vale"] is False


def test_importa_e_e_repetivel(matriz, banco, empresas):
    r = _importar(matriz, banco, "01")
    assert (r.cargos_criados, r.criados, r.atualizados, r.telefones) == (2, 2, 0, 2)
    assert any("CPF inválido" in a and "BRUNO" in a for a in r.avisos)

    r = _importar(matriz, banco, "01")
    assert (r.cargos_criados, r.criados, r.atualizados, r.telefones) == (0, 0, 2, 0)

    with banco() as db:
        ana = db.scalar(select(Funcionario).where(Funcionario.apelido == "ANINHA"))
        assert ana.cpf == "52998224725"
        assert ana.empresa_id == empresas["01"]
        assert ana.cargo.nome == "VENDEDOR"
        assert ana.criado_em.date() == date(2015, 3, 1)
        # o telefone de cliente (tipo_ter C) com o mesmo código não entra
        assert sorted((t.numero, t.tipo) for t in ana.telefones) == [("33334444", "1"), ("62999990000", "3")]
        assert db.scalar(select(Funcionario).where(Funcionario.apelido == "BRUNO")).cpf is None


def test_mesmo_codigo_em_outra_filial_e_outra_pessoa(matriz, tmp_path, banco, empresas):
    _importar(matriz, banco, "01")
    # na filial 03, o código 001 é de outra pessoa, e o cargo 001 tem outro nome
    carla = {**_ANA, "nome_fun": "CARLA FICTICIA", "guerra_fun": "CARLA", "cpf_fun": "111.444.777-35", "cod_car": "001"}
    filial = _banco_vb6(tmp_path / "f03.db", [carla], [("001", "Caixa", "N")])
    r = _importar(filial, banco, "03")
    filial.dispose()
    assert (r.criados, r.cargos_criados) == (1, 0)  # o cargo CAIXA já existia (nome igual, sem diferenciar caixa)
    with banco() as db:
        carla_nova = db.scalar(select(Funcionario).where(Funcionario.apelido == "CARLA"))
        assert carla_nova.empresa_id == empresas["03"]
        assert carla_nova.cargo.nome == "CAIXA"
        assert db.scalar(select(Funcionario).where(Funcionario.apelido == "ANINHA")).cargo.nome == "VENDEDOR"
        assert len(db.scalars(select(Cargo)).all()) == 2


def test_mesma_pessoa_em_duas_filiais_e_ligada_pelo_cpf(matriz, tmp_path, banco, empresas):
    _importar(matriz, banco, "01")
    ana_na_filial = {**_ANA, "cod_fun": "007", "guerra_fun": "ANA F"}
    filial = _banco_vb6(tmp_path / "f03.db", [ana_na_filial], [("001", "VENDEDOR", "S")], [(7, "62977776666", "3", "U")])
    r = _importar(filial, banco, "03")
    filial.dispose()
    assert (r.criados, r.ligados_por_cpf, r.telefones) == (0, 1, 1)
    with banco() as db:
        ana = db.scalar(select(Funcionario).where(Funcionario.cpf == "52998224725"))
        assert ana.apelido == "ANINHA"  # não sobrescreve com os dados da segunda filial
        assert ana.empresa_id == empresas["01"]
        assert len(ana.telefones) == 3


def test_reimportar_atualiza_mas_mantem_a_loja(matriz, banco, empresas):
    _importar(matriz, banco, "01")
    with banco() as db:
        ana = db.scalar(select(Funcionario).where(Funcionario.apelido == "ANINHA"))
        ana.empresa_id = empresas["03"]  # transferida no sistema novo
        db.commit()
    with matriz.begin() as c:
        c.execute(text("UPDATE tab_funcionarios SET nome_fun = 'ANA FICTICIA SILVA' WHERE cod_fun = '001'"))
    _importar(matriz, banco, "01")
    with banco() as db:
        ana = db.scalar(select(Funcionario).where(Funcionario.apelido == "ANINHA"))
        assert ana.nome == "ANA FICTICIA SILVA"
        assert ana.empresa_id == empresas["03"]


def test_empresa_precisa_existir(matriz, banco):
    with pytest.raises(EmpresaNaoImportada):
        _importar(matriz, banco, "01")


def test_nomes_compativeis():
    from etl.funcionarios import nomes_compativeis
    assert nomes_compativeis("ANA", "Ana Fictícia Souza")
    assert nomes_compativeis("ANAC", "ANA C SOUZA")  # abreviado e colado
    assert nomes_compativeis("MARIA ANA FICTICIA", "ANA FICTICIA SOUZA")  # um nome a mais na frente
    assert not nomes_compativeis("ANA FICTICIA", "SHOPPING CENTRO")
    assert not nomes_compativeis("ANA DE SOUZA", "BIA DE SOUZA")  # só a ligação e um sobrenome em comum


def _filial(tmp_path, nome, funcionarios, telefones=()):
    return _banco_vb6(tmp_path / nome, funcionarios, [("001", "VENDEDOR", "S")], telefones)


def test_cpf_do_dono_em_cadastro_que_nao_e_pessoa(tmp_path, banco, empresas):
    loja = {**_ANA, "cod_fun": "009", "nome_fun": "SHOPPING CENTRO", "guerra_fun": "SHOP"}
    eng = _filial(tmp_path, "f01.db", [_ANA, loja])
    r = _importar(eng, banco, "01")
    eng.dispose()
    assert r.criados == 2
    assert any("SHOPPING CENTRO" in a and "cadastrado à parte" in a for a in r.avisos)
    with banco() as db:
        assert db.scalar(select(Funcionario).where(Funcionario.apelido == "SHOP")).cpf is None
        assert db.scalar(select(Funcionario).where(Funcionario.apelido == "ANINHA")).cpf == "52998224725"


def test_sem_cpf_liga_pelo_nome_so_entre_filiais(tmp_path, banco, empresas):
    dani = {**_ANA, "cod_fun": "003", "nome_fun": "Dani  Fictícia", "guerra_fun": "DANI", "cpf_fun": "000.000.000-01"}
    homonima = {**dani, "cod_fun": "004", "guerra_fun": "DANI 2"}
    m = _filial(tmp_path, "f01.db", [dani, homonima])
    r = _importar(m, banco, "01")
    m.dispose()
    assert (r.criados, r.ligados_por_nome) == (2, 0)  # mesmo nome na mesma filial: duas pessoas

    f = _filial(tmp_path, "f03.db", [{**dani, "cod_fun": "010", "nome_fun": "DANI FICTICIA", "cpf_fun": ""}])
    r = _importar(f, banco, "03")
    f.dispose()
    assert r.criados == 1  # há duas DANI na 01: não dá para saber qual é
    with banco() as db:
        assert len(db.scalars(select(Funcionario)).all()) == 3


def test_mesmo_nome_sem_cpf_em_outra_filial_vira_um_cadastro(tmp_path, banco, empresas):
    dani = {**_ANA, "cod_fun": "003", "nome_fun": "DANI FICTICIA", "guerra_fun": "DANI", "cpf_fun": ""}
    m = _filial(tmp_path, "f01.db", [dani])
    _importar(m, banco, "01")
    m.dispose()
    f = _filial(tmp_path, "f03.db", [{**dani, "cod_fun": "010", "cpf_fun": "111.444.777-35", "rg_fun": None}])
    r = _importar(f, banco, "03")
    f.dispose()
    assert (r.criados, r.ligados_por_nome) == (0, 1)
    with banco() as db:
        dani_nova = db.scalar(select(Funcionario))
        assert dani_nova.cpf == "11144477735"  # o CPF que faltava vem da outra filial
        assert dani_nova.empresa_id == empresas["01"]


def test_ativa_em_outra_filial_muda_de_loja(tmp_path, banco, empresas):
    saiu = {**_ANA, "status_fun": "2", "guerra_fun": "ANA 01"}
    m = _filial(tmp_path, "f01.db", [saiu])
    _importar(m, banco, "01")
    f = _filial(tmp_path, "f03.db", [{**_ANA, "cod_fun": "020", "guerra_fun": "ANA 03"}])
    r = _importar(f, banco, "03")
    assert r.mudaram_de_loja == 1
    _importar(m, banco, "01")  # reimportar a 01, onde está inativa, não desfaz
    _importar(f, banco, "03")
    m.dispose()
    f.dispose()
    with banco() as db:
        ana = db.scalar(select(Funcionario))
        assert (ana.empresa_id, ana.ativo, ana.apelido) == (empresas["03"], True, "ANA 03")


def test_reimportar_a_outra_filial_nao_sobrescreve(matriz, tmp_path, banco, empresas):
    _importar(matriz, banco, "01")
    f = _filial(tmp_path, "f03.db", [{**_ANA, "cod_fun": "007", "guerra_fun": "ANA F", "nome_fun": "ANA F SOUZA"}])
    _importar(f, banco, "03")
    r = _importar(f, banco, "03")
    f.dispose()
    assert r.atualizados == 1
    with banco() as db:
        ana = db.scalar(select(Funcionario).where(Funcionario.cpf == "52998224725"))
        assert (ana.nome, ana.apelido) == ("ANA FICTICIA", "ANINHA")
