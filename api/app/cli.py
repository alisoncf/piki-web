"""Comandos de administração, para usar antes de existir a tela de cadastro.

    python -m app.cli sincronizar-permissoes
    python -m app.cli criar-empresa --codigo 01 --nome "Loja Centro" [--cnpj 11222333000181]
    python -m app.cli criar-perfil --nome Gerente --permissoes acesso.usuarios,acesso.perfis
    python -m app.cli criar-usuario --login maria --nome "Maria da Silva" [--admin]
    python -m app.cli dar-acesso --login maria --empresa 01 --perfil Gerente
"""
import argparse
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.registro_modelos  # noqa: F401  (todos os modelos, para as relações entre domínios)
from app.dominios.acesso import repositorio as repo
from app.dominios.acesso import servico
from app.dominios.empresas import servico as empresas
from app.dominios.empresas.esquemas import EmpresaNova
from app.dominios.empresas.modelos import Empresa
from app.nucleo.banco import engine


def _falha(msg: str) -> None:
    print(f"erro: {msg}", file=sys.stderr)
    sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="python -m app.cli")
    sub = p.add_subparsers(dest="comando", required=True)

    sub.add_parser("sincronizar-permissoes", help="grava no banco o catálogo de permissões do código")

    # a primeira empresa: sem nenhuma, nem o administrador consegue entrar para usar a tela de empresas
    e = sub.add_parser("criar-empresa")
    e.add_argument("--codigo", required=True, help="código da filial no VB6 (cod_emp), 2 dígitos")
    e.add_argument("--nome", required=True)
    e.add_argument("--cnpj")
    e.add_argument("--razao-social")

    pf = sub.add_parser("criar-perfil")
    pf.add_argument("--nome", required=True)
    pf.add_argument("--permissoes", default="", help="códigos separados por vírgula")

    u = sub.add_parser("criar-usuario")
    u.add_argument("--login", required=True)
    u.add_argument("--nome", required=True)
    u.add_argument("--admin", action="store_true", help="acesso total a todas as empresas")

    a = sub.add_parser("dar-acesso")
    a.add_argument("--login", required=True)
    a.add_argument("--empresa", required=True, help="código da empresa")
    a.add_argument("--perfil", required=True, help="nome do perfil")

    args = p.parse_args(argv)
    with Session(engine()) as db:
        if args.comando == "sincronizar-permissoes":
            print(f"{servico.sincronizar_permissoes(db)} permissões novas")
        elif args.comando == "criar-empresa":
            try:
                dados = EmpresaNova(codigo=args.codigo, nome=args.nome, cnpj=args.cnpj, razao_social=args.razao_social)
                emp = empresas.criar_empresa(db, dados)
            except (ValueError, empresas.ErroEmpresa) as erro:
                _falha(str(erro))
            print(f"empresa {emp.codigo} criada (id {emp.id})")
        elif args.comando == "criar-perfil":
            perms = [x.strip() for x in args.permissoes.split(",") if x.strip()]
            try:
                perfil = servico.criar_perfil(db, args.nome, perms)
            except ValueError as erro:
                _falha(str(erro))
            print(f"perfil {perfil.nome} criado com {len(perfil.permissoes)} permissões")
        elif args.comando == "criar-usuario":
            senha = getpass.getpass("senha: ")
            if not senha or senha != getpass.getpass("repita a senha: "):
                _falha("as senhas não conferem")
            usu = servico.criar_usuario(db, args.login, args.nome, senha, args.admin)
            print(f"usuário {usu.login} criado (id {usu.id})")
        elif args.comando == "dar-acesso":
            usu = repo.usuario_por_login(db, args.login)
            emp = db.scalar(select(Empresa).where(Empresa.codigo == args.empresa))
            perfil = repo.perfil_por_nome(db, args.perfil)
            if not (usu and emp and perfil):
                _falha("usuário, empresa ou perfil não encontrado")
            servico.dar_acesso(db, usu, emp, perfil)
            print(f"{usu.login} → empresa {emp.codigo} como {perfil.nome}")


if __name__ == "__main__":
    main()
