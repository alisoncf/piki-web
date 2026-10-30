"""Comandos do ETL.

    python -m etl empresas --origem "mysql+pymysql://usuario:senha@servidor:3306/requinte"
    python -m etl funcionarios --origem "mysql+pymysql://..." --empresa 01

A origem é o banco MariaDB de uma filial (ou a cópia dele na área de
chegada). O destino é o banco do .env (PIKI_DATABASE_URL). Para ler MariaDB,
instale o extra: pip install -e ".[legado]".
"""
import argparse
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.nucleo.banco import engine
from etl.empresas import ConflitoEmpresa, importar_empresas
from etl.funcionarios import EmpresaNaoImportada, importar_funcionarios


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="python -m etl")
    sub = p.add_subparsers(dest="comando", required=True)
    e = sub.add_parser("empresas", help="importa as empresas da tabela sped_empresa")
    e.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    f = sub.add_parser("funcionarios", help="importa cargos, funcionários e seus telefones")
    f.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    f.add_argument("--empresa", required=True, help="código da empresa (cod_emp) dona deste banco")
    args = p.parse_args(argv)

    origem = create_engine(args.origem)
    try:
        with origem.connect() as conexao, Session(engine()) as db:
            if args.comando == "empresas":
                r = importar_empresas(conexao, db)
                print(f"criadas: {', '.join(r.criadas) or 'nenhuma'}")
                print(f"atualizadas: {', '.join(r.atualizadas) or 'nenhuma'}")
            elif args.comando == "funcionarios":
                r = importar_funcionarios(conexao, db, args.empresa)
                print(f"cargos novos: {r.cargos_criados}")
                print(f"funcionários: {r.criados} novos, {r.atualizados} atualizados, "
                      f"{r.ligados_por_cpf} já existentes em outra filial (pelo CPF)")
                print(f"telefones novos: {r.telefones}")
                for aviso in r.avisos:
                    print(f"aviso: {aviso}")
    except (ConflitoEmpresa, EmpresaNaoImportada) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        sys.exit(1)
    finally:
        origem.dispose()


if __name__ == "__main__":
    main()
