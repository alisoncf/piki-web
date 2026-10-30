# piki-web

Nova versão do Piki, o sistema de gestão comercial (PDV, caixa, financeiro, estoque, consignação, NF-e/NFC-e e SPED) hoje escrito em VB6 + MariaDB, com um banco separado em cada filial.

A nova versão tem um banco único para todas as empresas do grupo, com cadastro de clientes e produtos compartilhado, estoque e notas por empresa, e usuários que podem trabalhar em mais de uma empresa. Os dados antigos chegam por ETL, e cada filial vira para o sistema novo quando as telas que ela usa estiverem prontas.

## Stack

- **API:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic
- **Banco:** PostgreSQL ou MariaDB (decisão P7 em aberto); SQLite para desenvolvimento
- **Web:** Vue 3 + Quasar (próxima etapa)

## Estrutura

```
api/
  app/
    nucleo/         # banco, segurança, permissões, contexto da requisição (usuário + empresa)
    dominios/       # um domínio por pasta: modelos, esquemas, repositorio, servico, rotas
      acesso/       # empresas, usuários, perfis, permissões, login
      sistema/      # /saude
    cli.py          # comandos de administração
  alembic/          # migrações da estrutura do banco
  etl/              # importação dos dados do VB6
  tests/
web/                # Vue/Quasar (ainda não criado)
docs/
  roteiro.md        # o que já foi feito e o que vem a seguir
  decisoes.md       # decisões de arquitetura e pendências
  legado/           # inventário do sistema VB6, mapa de tabelas e schema antigo
```

## Rodando a API

```bash
cd api
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -e ".[dev]"          # acrescente ,mariadb ou ,postgres para o driver do banco
cp ../.env.example ../.env       # opcional: sem .env, usa SQLite local

alembic upgrade head             # cria as tabelas

# primeiro acesso
python -m app.cli criar-empresa --codigo 01 --nome "Loja Centro"
python -m app.cli criar-usuario --login admin --nome "Administrador" --admin

uvicorn app.main:app --reload
```

A documentação interativa fica em http://localhost:8000/docs. Para testar: `POST /auth/login`, copie o `access_token`, clique em **Authorize** e use as demais rotas.

Testes:

```bash
cd api
pytest
```

## Onde estamos

O caminho do projeto, com o que já foi feito e o que vem a seguir, está em [`docs/roteiro.md`](docs/roteiro.md). As decisões e as perguntas em aberto ficam em [`docs/decisoes.md`](docs/decisoes.md).

## Segurança

Credenciais ficam só no arquivo `.env`, que não vai para o Git. Nunca coloque senha, usuário de banco ou chave de API no código.
