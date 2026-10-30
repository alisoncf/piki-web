"""Comandos do ETL.

    python -m etl empresas --origem "mysql+pymysql://usuario:senha@servidor:3306/requinte"

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


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="python -m etl")
    sub = p.add_subparsers(dest="comando", required=True)
    e = sub.add_parser("empresas", help="importa as empresas da tabela sped_empresa")
    e.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    args = p.parse_args(argv)

    origem = create_engine(args.origem)
    try:
        with origem.connect() as conexao, Session(engine()) as db:
            if args.comando == "empresas":
                r = importar_empresas(conexao, db)
                print(f"criadas: {', '.join(r.criadas) or 'nenhuma'}")
                print(f"atualizadas: {', '.join(r.atualizadas) or 'nenhuma'}")
    except ConflitoEmpresa as erro:
        print(f"erro: {erro}", file=sys.stderr)
        sys.exit(1)
    finally:
        origem.dispose()


if __name__ == "__main__":
    main()
