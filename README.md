# piki-web

Nova versão do Piki, o sistema de gestão comercial (PDV, caixa, financeiro, estoque, consignação, NF-e/NFC-e e SPED) hoje escrito em VB6 + MariaDB, com um banco separado em cada filial.

A nova versão tem um banco único para todas as empresas do grupo, com cadastro de clientes e produtos compartilhado, estoque e notas por empresa, e usuários que podem trabalhar em mais de uma empresa. Os dados antigos chegam por ETL, e cada filial vira para o sistema novo quando as telas que ela usa estiverem prontas.

## Stack

- **API:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic
- **Banco:** PostgreSQL 16+ (decisão D12); as filiais seguem em MariaDB até a virada
- **Web:** Vue 3 + Quasar + Pinia, com Vite

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
web/                # Vue/Quasar (ver web/README.md)
docker-compose.yml  # PostgreSQL de desenvolvimento
docs/
  roteiro.md        # o que já foi feito e o que vem a seguir
  decisoes.md       # decisões de arquitetura e pendências
  legado/           # inventário do sistema VB6, mapa de tabelas e schema antigo
```

## Rodando a API

Pré-requisitos: Python 3.12+ e Docker (para o PostgreSQL). Sem Docker, dá para rodar tudo com SQLite: basta não criar o `.env`.

```bash
docker compose up -d             # sobe o PostgreSQL na porta 5433 (bancos piki e piki_teste)
cp .env.example .env

cd api
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -e ".[dev]"

alembic upgrade head             # cria as tabelas

# primeiro acesso
python -m app.cli criar-empresa --codigo 01 --nome "Loja Centro"
python -m app.cli criar-usuario --login admin --nome "Administrador" --admin

uvicorn app.main:app --reload
```

A documentação interativa fica em http://localhost:8000/docs.

## Rodando o front-end

Pré-requisito: Node.js 20+. Com a API rodando, em outro terminal:

```bash
cd web
npm install
npm run dev
```

Abra http://localhost:9000 e entre com o usuário criado acima.

Testes:

```bash
cd api && pytest      # API: SQLite em memória, ou o PostgreSQL se PIKI_TESTE_DATABASE_URL estiver no .env
cd web && npm test    # front-end
```

## Onde estamos

O caminho do projeto, com o que já foi feito e o que vem a seguir, está em [`docs/roteiro.md`](docs/roteiro.md). As decisões e as perguntas em aberto ficam em [`docs/decisoes.md`](docs/decisoes.md), e as convenções de código em [`CLAUDE.md`](CLAUDE.md).

## Segurança

Credenciais ficam só no arquivo `.env`, que não vai para o Git. Nunca coloque senha, usuário de banco ou chave de API no código.
