"""Comandos do ETL.

    python -m etl empresas --origem "mysql+pymysql://usuario:senha@servidor:3306/requinte"
    python -m etl funcionarios --origem "mysql+pymysql://..." --empresa 01
    python -m etl clientes --origem "mysql+pymysql://..." --empresa 01 --avisos avisos-01.txt
    python -m etl fornecedores --origem "mysql+pymysql://..." --empresa 01
    python -m etl usuarios --origem "mysql+pymysql://..." --empresa 01
    python -m etl caixa --origem "mysql+pymysql://..." --empresa 01
    python -m etl estoque --origem "mysql+pymysql://..." --empresa 02
    python -m etl receber --origem "mysql+pymysql://..." --empresa 01 --avisos avisos-receber-01.txt
    python -m etl produtos --origem "mysql+pymysql://.../requinte" --empresa 01 --outras "mysql+pymysql://.../requintejun"

Para um MariaDB local em que o root entra pela autenticação do Windows (sem
senha), use o conector da MariaDB: mariadb+mariadbconnector://root@127.0.0.1:3306/requinte

A origem é o banco MariaDB de uma filial (ou a cópia dele na área de
chegada). O destino é o banco do .env (PIKI_DATABASE_URL). Para ler MariaDB,
instale o extra: pip install -e ".[legado]".
"""
import argparse
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.registro_modelos  # noqa: F401 (todos os modelos, para as relações entre domínios)
from app.nucleo.banco import engine
from etl.caixa import importar_caixa
from etl.clientes import importar_clientes
from etl.empresas import ConflitoEmpresa, importar_empresas
from etl.fornecedores import importar_fornecedores
from etl.estoque import importar_estoque
from etl.funcionarios import EmpresaNaoImportada, importar_funcionarios
from etl.produtos import importar_produtos
from etl.receber import importar_receber
from etl.usuarios import importar_usuarios


def _avisos(avisos: list[str], arquivo: str | None, na_tela: int = 30) -> None:
    for aviso in avisos[:na_tela]:
        print(f"aviso: {aviso}")
    if arquivo:
        with open(arquivo, "w", encoding="utf-8") as f:
            f.writelines(f"{a}\n" for a in avisos)
        print(f"{len(avisos)} avisos gravados em {arquivo}")
    elif len(avisos) > na_tela:
        print(f"... e mais {len(avisos) - na_tela} avisos (use --avisos arquivo.txt para ver todos)")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="python -m etl")
    sub = p.add_subparsers(dest="comando", required=True)
    e = sub.add_parser("empresas", help="importa as empresas da tabela sped_empresa")
    e.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    f = sub.add_parser("funcionarios", help="importa cargos, funcionários e seus telefones")
    f.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    f.add_argument("--empresa", required=True, help="código da empresa (cod_emp) dona deste banco")
    c = sub.add_parser("clientes", help="importa grupos, setores, órgãos, clientes, telefones, referências e anotações")
    c.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    c.add_argument("--empresa", required=True, help="código da empresa (cod_emp) dona deste banco")
    c.add_argument("--avisos", help="arquivo para gravar todos os avisos (na tela saem só os primeiros)")
    fo = sub.add_parser("fornecedores", help="importa fornecedores, com telefones e contatos")
    fo.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    fo.add_argument("--empresa", required=True, help="código da empresa (cod_emp) dona deste banco")
    fo.add_argument("--avisos", help="arquivo para gravar todos os avisos (na tela saem só os primeiros)")
    u = sub.add_parser("usuarios", help="importa os usuários (depois dos funcionários), com o perfil do nível")
    u.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    u.add_argument("--empresa", required=True, help="código da empresa (cod_emp) dona deste banco")
    pr = sub.add_parser("produtos", help="importa seções, subseções e produtos do banco da matriz (depois dos fornecedores)")
    pr.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6 da matriz")
    pr.add_argument("--empresa", required=True, help="código da empresa (cod_emp) dona deste banco")
    pr.add_argument("--outras", nargs="*", default=[],
                    help="bancos das outras lojas, só para ver o que vendeu ou comprou no último ano (produto ativo)")
    pr.add_argument("--avisos", help="arquivo para gravar todos os avisos (na tela saem só os primeiros)")
    es = sub.add_parser("estoque", help="importa o saldo, o reservado e a localização de uma loja (depois dos produtos)")
    es.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    es.add_argument("--empresa", required=True, help="código da empresa (cod_emp) dona deste banco")
    es.add_argument("--avisos", help="arquivo para gravar todos os avisos (na tela saem só os primeiros)")
    cx = sub.add_parser("caixa", help="importa as formas de pagamento e os caixas de uma loja")
    cx.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    cx.add_argument("--empresa", required=True, help="código da empresa (cod_emp) dona deste banco")
    rc = sub.add_parser("receber", help="importa as contas a receber de clientes em aberto (depois dos clientes e usuários)")
    rc.add_argument("--origem", required=True, help="URL SQLAlchemy do banco do VB6")
    rc.add_argument("--empresa", required=True, help="código da empresa (cod_emp) dona deste banco")
    rc.add_argument("--avisos", help="arquivo para gravar todos os avisos (na tela saem só os primeiros)")
    args = p.parse_args(argv)
    # no Windows a saída redirecionada usa cp1252, que não tem os caracteres estranhos de alguns nomes antigos
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

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
                      f"{r.ligados_por_cpf + r.ligados_por_nome} já existentes "
                      f"({r.ligados_por_cpf} pelo CPF, {r.ligados_por_nome} pelo nome), "
                      f"{r.mudaram_de_loja} mudaram de loja")
                print(f"telefones novos: {r.telefones}")
                for aviso in r.avisos:
                    print(f"aviso: {aviso}")
            elif args.comando == "clientes":
                r = importar_clientes(conexao, db, args.empresa)
                print(f"grupos novos: {r.grupos_criados}, parentescos novos: {r.parentescos_criados}, "
                      f"órgãos novos: {r.orgaos_criados}")
                print(f"setores novos: {r.setores_criados} ({r.setores_sem_cidade} desta loja sem cidade), "
                      f"cobradores ligados a setores: {r.cobradores}, funcionários com setor: {r.funcionarios_no_setor}")
                print(f"clientes: {r.criados} novos ({r.sem_documento} sem CPF/CNPJ válido), "
                      f"{r.atualizados} atualizados, {r.ligados_por_documento} juntados pelo CPF/CNPJ a um cadastro que já existia")
                print(f"telefones novos: {r.telefones}, referências: {r.referencias}, anotações: {r.anotacoes}")
                print(f"descartados (sem CPF/CNPJ válido ou nome sem sentido): {r.descartados}, "
                      f"excluídos do banco novo: {r.excluidos}, mantidos por dívida em aberto: {r.mantidos_por_divida}, "
                      f"nomes corrigidos: {r.nomes_corrigidos}")
                _avisos(r.avisos, args.avisos)
            elif args.comando == "usuarios":
                r = importar_usuarios(conexao, db, args.empresa)
                print(f"perfis novos: {r.perfis_criados}")
                print(f"usuários: {r.criados} novos, {r.ligados} já existentes; acessos novos: {r.acessos_criados}, "
                      f"acessos desligados (inativos no VB6): {r.desligados}")
                _avisos(r.avisos, None)
            elif args.comando == "fornecedores":
                r = importar_fornecedores(conexao, db, args.empresa)
                print(f"fornecedores: {r.criados} novos, {r.atualizados} atualizados, "
                      f"{r.ligados_por_documento} juntados pelo CPF/CNPJ a um cadastro que já existia")
                print(f"telefones novos: {r.telefones}, contatos novos: {r.contatos}")
                print(f"descartados (sem CPF/CNPJ válido ou nome sem sentido): {r.descartados}, "
                      f"excluídos do banco novo: {r.excluidos}")
                _avisos(r.avisos, args.avisos)
            elif args.comando == "produtos":
                outras = [create_engine(url) for url in args.outras]
                try:
                    conexoes = [o.connect() for o in outras]
                    r = importar_produtos(conexao, db, args.empresa, conexoes)
                finally:
                    for o in outras:
                        o.dispose()
                print(f"seções novas: {r.secoes}, subseções novas: {r.subsecoes}")
                print(f"produtos: {r.criados} novos, {r.atualizados} atualizados; {r.ativos} ativos, {r.inativos} inativos "
                      f"(sem venda, compra ou alteração no último ano); {r.fracionados} aceitam fração")
                print(f"códigos de barras novos: {r.codigos_barras}, fornecedores ligados: {r.fornecedores}")
                _avisos(r.avisos, args.avisos)
            elif args.comando == "estoque":
                r = importar_estoque(conexao, db, args.empresa)
                print(f"linhas de estoque novas: {r.linhas}, movimentos de saldo: {r.movimentos}, "
                      f"produtos com saldo negativo: {r.negativos}, códigos que não são da matriz: {r.ignorados}")
                _avisos(r.avisos, args.avisos)
            elif args.comando == "caixa":
                r = importar_caixa(conexao, db, args.empresa)
                print(f"formas de pagamento novas: {r.formas}, caixas novos: {r.caixas}")
                _avisos(r.avisos, None)
            elif args.comando == "receber":
                r = importar_receber(conexao, db, args.empresa)
                print(f"contas novas: {r.contas}, parcelas novas: {r.parcelas}, parcelas atualizadas: {r.atualizadas}")
                print(f"em aberto: {r.parcelas_em_aberto} parcelas, R$ {r.em_aberto}; "
                      f"documentos de cliente não importado: {r.sem_cliente}")
                for linha in r.fora:
                    print(f"fora: {linha}")
                _avisos(r.avisos, args.avisos)
    except (ConflitoEmpresa, EmpresaNaoImportada) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        sys.exit(1)
    finally:
        origem.dispose()


if __name__ == "__main__":
    main()
