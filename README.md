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

Testes:

```bash
cd api
pytest
```

## Onde estamos

O plano completo está em [`docs/legado/README.md`](docs/legado/README.md). As ondas de migração são:

| Onda | Escopo | Status |
|---|---|---|
| 0 | Fundação: API, conexão com o banco, login, menu | em andamento |
| 1 | Cadastros | pendente |
| 2 | Relatórios | pendente |
| 3 | Financeiro | pendente |
| 4 | Estoque e compras | pendente |
| 5 | Consignação e representantes | pendente |
| 6 | Fiscal (NF-e/NFC-e via ACBrMonitor, SPED) | pendente |
| 7 | PDV e caixa | pendente |

O acompanhamento tela a tela fica nas colunas `status_migracao` e `destino_novo` de [`docs/legado/inventario.csv`](docs/legado/inventario.csv).

## Segurança

Credenciais ficam só no arquivo `.env`, que não vai para o Git. Nunca coloque senha, usuário de banco ou chave de API no código.
