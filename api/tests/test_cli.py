from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import cli
from app.dominios.acesso.modelos import Usuario, UsuarioEmpresa
from app.registro_modelos import Base


def test_fluxo_de_administracao(tmp_path, monkeypatch, capsys):
    eng = create_engine(f"sqlite:///{tmp_path / 'cli.db'}")
    Base.metadata.create_all(eng)
    monkeypatch.setattr(cli, "engine", lambda: eng)
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt="": "segredo")

    cli.main(["sincronizar-permissoes"])
    cli.main(["criar-empresa", "--codigo", "01", "--nome", "Loja Centro"])
    cli.main(["criar-perfil", "--nome", "Gerente", "--permissoes", "acesso.usuarios"])
    cli.main(["criar-usuario", "--login", "maria", "--nome", "Maria"])
    cli.main(["dar-acesso", "--login", "maria", "--empresa", "01", "--perfil", "Gerente"])

    saida = capsys.readouterr().out
    assert "maria → empresa 01 como Gerente" in saida
    with Session(eng) as db:
        usuario = db.scalar(select(Usuario).where(Usuario.login == "maria"))
        assert usuario.hash_senha.startswith("$argon2")
        assert db.get(UsuarioEmpresa, (usuario.id, 1)) is not None
