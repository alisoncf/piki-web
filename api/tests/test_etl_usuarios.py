"""ETL de usuários (D23). Dados fictícios."""
import pytest
from sqlalchemy import create_engine, select, text

from app.dominios.acesso.modelos import Perfil, Usuario, UsuarioEmpresa
from app.dominios.acesso.servico import autenticar, criar_usuario
from app.dominios.empresas.esquemas import EmpresaNova
from app.dominios.empresas.servico import criar_empresa
from app.dominios.funcionarios.modelos import Funcionario
from etl import mapa
from etl.funcionarios import EmpresaNaoImportada
from etl.senha_legado import codificar
from etl.usuarios import importar_usuarios


def _banco_vb6(caminho, usuarios, funcionarios):
    """usuarios: (cod_fun, nivel, senha, status); funcionarios: (cod_fun, status_fun)."""
    eng = create_engine(f"sqlite:///{caminho}")
    with eng.begin() as c:
        c.execute(text("CREATE TABLE tab_usuarios (COD_FUN TEXT PRIMARY KEY, ULTACESSO_USU TEXT, NIVEL_USU TEXT,"
                       " SENHA_USU TEXT, Status_USU TEXT, corfundo_usu TEXT)"))
        c.execute(text("CREATE TABLE tab_funcionarios (cod_fun TEXT PRIMARY KEY, status_fun TEXT)"))
        for cod, nivel, senha, status in usuarios:
            c.execute(text("INSERT INTO tab_usuarios (COD_FUN, NIVEL_USU, SENHA_USU, Status_USU) VALUES (:c, :n, :s, :st)"),
                      {"c": cod, "n": nivel, "s": codificar(senha) if senha else "", "st": status})
        for cod, status in funcionarios:
            c.execute(text("INSERT INTO tab_funcionarios VALUES (:c, :s)"), {"c": cod, "s": status})
    return eng


@pytest.fixture
def cenario(banco):
    """Matriz e filial; a ANA (lotada na matriz) tem um código em cada uma."""
    with banco() as db:
        e1 = criar_empresa(db, EmpresaNova(codigo="01", nome="MATRIZ"))
        e2 = criar_empresa(db, EmpresaNova(codigo="02", nome="FILIAL"))
        pessoas = {}
        for chave, nome, apelido in (("ana", "Ana Ficticia", "ANA"), ("beto", "Beto Ficticio", "BETO"),
                                     ("caio", "Caio Ficticio", "CAIO"), ("ana2", "Ana Outra", "ANA"),
                                     ("alison", "Alison Ficticio", "ALISON")):
            f = Funcionario(nome=nome, apelido=apelido, empresa_id=e1.id)
            db.add(f)
            db.flush()
            pessoas[chave] = f.id
        for cod, chave in (("001", "ana"), ("002", "beto"), ("003", "caio"), ("005", "ana2"), ("000", "alison")):
            mapa.gravar(db, "tab_funcionarios", e1.id, cod, pessoas[chave])
        mapa.gravar(db, "tab_funcionarios", e2.id, "010", pessoas["ana"])
        criar_usuario(db, "alison", "Alison", "senha-do-sistema-novo", administrador=True)
        db.commit()
        return {"01": e1.id, "02": e2.id, **pessoas}


def _importar(eng, banco, codigo):
    with eng.connect() as c, banco() as db:
        return importar_usuarios(c, db, codigo)


def test_empresa_precisa_existir(banco, tmp_path):
    eng = _banco_vb6(tmp_path / "v.db", [], [])
    with pytest.raises(EmpresaNaoImportada):
        _importar(eng, banco, "01")
    eng.dispose()


def test_importa_usuarios(banco, cenario, tmp_path):
    matriz = _banco_vb6(tmp_path / "m.db", [
        ("001", "3", "abc123", "1"),
        ("002", "1", "xyz", "0"),  # usuário inativo
        ("003", "1", "xyz", "1"),  # funcionário inativo
        ("004", "1", "xyz", "1"),  # funcionário que não foi importado
        ("005", "2", "outra1", "1"),  # outra pessoa com o mesmo apelido
        ("000", "4", "velha", "1"),  # já existe como administrador, criado pela linha de comando
    ], [("001", "1"), ("002", "1"), ("003", "0"), ("004", "1"), ("005", "1"), ("000", "1")])
    r = _importar(matriz, banco, "01")
    assert (r.criados, r.ligados, r.acessos_criados, r.perfis_criados) == (2, 1, 2, 4)
    assert any("usuário 004" in a for a in r.avisos)
    with banco() as db:
        ana = db.scalar(select(Usuario).where(Usuario.funcionario_id == cenario["ana"]))
        assert (ana.login, ana.nome, ana.trocar_senha, ana.senha_sem_caixa) == ("ana", "Ana Ficticia", True, True)
        assert autenticar(db, "ana", "ABC123").id == ana.id  # como no VB6, sem diferenciar maiúsculas
        assert [(a.empresa.codigo, a.perfil.nome) for a in ana.acessos] == [("01", "Gerente")]
        outra = db.scalar(select(Usuario).where(Usuario.funcionario_id == cenario["ana2"]))
        assert (outra.login, outra.acessos[0].perfil.nome) == ("ana2", "Supervisor")
        # o administrador é ligado ao funcionário, mas a senha do sistema novo continua
        alison = db.scalar(select(Usuario).where(Usuario.login == "alison"))
        assert (alison.funcionario_id, alison.acessos) == (cenario["alison"], [])
        assert autenticar(db, "alison", "senha-do-sistema-novo").id == alison.id
        assert db.scalar(select(Usuario).where(Usuario.funcionario_id == cenario["beto"])) is None
        assert sorted(p.nome for p in db.scalars(select(Perfil))) == ["Gerente", "Gestor", "Operador", "Supervisor"]

    # na filial a ANA é operadora, com outra senha: a da matriz (lotação) continua
    filial = _banco_vb6(tmp_path / "f.db", [("010", "1", "filial1", "1")], [("010", "1")])
    r = _importar(filial, banco, "02")
    assert (r.criados, r.ligados) == (0, 1)
    with banco() as db:
        ana = db.scalar(select(Usuario).where(Usuario.funcionario_id == cenario["ana"]))
        assert sorted((a.empresa.codigo, a.perfil.nome) for a in ana.acessos) == [("01", "Gerente"), ("02", "Operador")]
        assert autenticar(db, "ana", "abc123").id == ana.id

    # reimportar não duplica; o perfil mudado na tela fica; quem ficou inativo perde o acesso daquela loja
    with banco() as db:
        vinculo = db.get(UsuarioEmpresa, (ana.id, cenario["01"]))
        vinculo.perfil_id = db.scalar(select(Perfil.id).where(Perfil.nome == "Gestor"))
        db.commit()
    with matriz.begin() as c:
        c.execute(text("UPDATE tab_usuarios SET Status_USU = '0' WHERE COD_FUN = '005'"))
    r = _importar(matriz, banco, "01")
    assert (r.criados, r.desligados) == (0, 1)
    with banco() as db:
        assert db.get(UsuarioEmpresa, (ana.id, cenario["01"])).perfil.nome == "Gestor"
        outra = db.scalar(select(Usuario).where(Usuario.funcionario_id == cenario["ana2"]))
        assert outra.acessos[0].ativo is False
    matriz.dispose()
    filial.dispose()
