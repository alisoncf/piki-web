# piki-web

Nova versão do Piki, o sistema de gestão comercial (PDV, caixa, financeiro, estoque, consignação, NF-e/NFC-e e SPED) hoje escrito em VB6 + MySQL/MariaDB.

A migração é gradual: o sistema antigo e o novo convivem, tela por tela, até o VB6 poder ser desligado. A nova versão também integra as filiais num banco único, identificando cada filial pelo `cod_emp`.

## Stack

- **API:** Python 3.12+, FastAPI, SQLAlchemy 2, MariaDB
- **Web:** Vue 3 + Quasar (próxima etapa)

## Estrutura

```
api/            # FastAPI
web/            # Vue/Quasar (ainda não criado)
docs/legado/    # inventário do sistema VB6, mapa de tabelas e schema atual
docs/roteiro.md   # o que já foi feito e o que vem a seguir
docs/decisoes.md  # decisões de arquitetura e pendências
```

## Rodando a API

```bash
cd api
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp ../.env.example ../.env       # e ajuste a conexão com o banco
uvicorn app.main:app --reload
```

A documentação interativa fica em http://localhost:8000/docs, e `GET /saude` confirma se a API está conectada ao banco.

Antes do primeiro login, aplique as migrações em `api/migracoes/` (por enquanto só a `001`, que cria a tabela `web_credencial` sem mexer nas tabelas do VB6). Depois, em `/docs`, use `POST /auth/login` com o apelido ou código do funcionário e a mesma senha do VB6.

Testes:

```bash
cd api
pytest
```

## Onde estamos

O caminho do projeto, com o que já foi feito e o que vem a seguir, está em [`docs/roteiro.md`](docs/roteiro.md). As decisões de arquitetura ficam em [`docs/decisoes.md`](docs/decisoes.md), e o acompanhamento tela a tela nas colunas `status_migracao` e `destino_novo` de [`docs/legado/inventario.csv`](docs/legado/inventario.csv).

## Segurança

Credenciais ficam só no arquivo `.env`, que não vai para o Git. Nunca coloque senha, usuário de banco ou chave de API no código.
