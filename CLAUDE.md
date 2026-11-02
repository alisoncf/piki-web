# CLAUDE.md

Guia para quem (pessoa ou IA) for trabalhar neste repositório. Leia antes de mudar qualquer coisa.

## O projeto

`piki-web` é a nova versão do Piki, sistema de gestão comercial (PDV, caixa, financeiro, estoque, consignação, NF-e/NFC-e, SPED) hoje em VB6 + MariaDB, com um banco separado em cada filial. O legado está em `alisoncf/piki_vb` (projeto em produção: `requinte/prj/piki_Simples.vbp`) e não deve ser alterado a partir daqui.

A nova versão tem banco único (PostgreSQL) para todas as empresas do grupo. Os dados das filiais chegam por ETL, e cada filial vira para o sistema novo quando as telas que ela usa estiverem prontas.

## Antes de começar uma tarefa

1. Leia `docs/roteiro.md`: onde estamos e o que vem a seguir.
2. Leia `docs/decisoes.md`: as decisões vigentes (D1, D5, D8 a D23) e as pendências (P1...). Não contrarie uma decisão vigente sem discutir com o Alison; se ela mudar, marque a antiga como substituída e registre a nova com data.
3. Para regras de negócio do VB6, consulte `docs/legado/` (inventário por tela, mapa de tabelas e schema antigo) e o código do legado.

## Regras do domínio (D9, D10)

- **Empresa** = filial com CNPJ próprio. Usuários acessam uma ou várias empresas, com um **perfil** em cada uma.
- **Cadastros globais** (clientes, produtos, fornecedores...): uma cópia só, sem empresa.
- **Dados por empresa** (estoque, preço e custo do produto, notas, vendas, caixa): sempre com `empresa_id`, e toda consulta filtra pela empresa ativa (`ctx.empresa_id`).
- **Contas a receber**: pertencem à empresa que vendeu, mas podem ser consultadas e recebidas em qualquer empresa; a baixa registra a empresa e o caixa de quem recebeu.
- Toda rota de negócio usa `Depends(exige("area.acao"))`. Permissão nova vai em `app/nucleo/permissoes.py`.

## Organização do código (D11)

```
api/app/nucleo/          banco, segurança, permissões, contexto (usuário + empresa ativa)
api/app/dominios/<nome>/ modelos.py, esquemas.py, repositorio.py, servico.py, rotas.py
api/alembic/versions/    migrações numeradas (0001, 0002...)
api/etl/                 importação do VB6
api/tests/
web/src/                 Vue 3 + Quasar + Pinia (ver web/README.md)
```

- `rotas.py` só traduz HTTP; regra de negócio fica em `servico.py`, que não importa nada do FastAPI e levanta erros de domínio; consultas ficam em `repositorio.py`.
- Domínio novo com tabelas: registre os modelos em `app/registro_modelos.py`, inclua o router em `app/main.py`.
- Mudou um modelo: gere a migração com `alembic revision --autogenerate --rev-id NNNN -m "..."`, revise o arquivo gerado e confira que roda no PostgreSQL. Nunca edite uma migração que já foi enviada; crie outra.
- Valores em dinheiro: `Numeric(14, 2)`, nunca float.
- Front-end: uma tela por arquivo em `web/src/paginas/<dominio>/`, rota com `meta.permissao` e item no `menu.js` com o mesmo código de permissão da API. O front só esconde; quem garante a permissão é a API.

## Convenções

- **Idioma:** português em nomes de tabelas, colunas, funções, variáveis, mensagens, commits e documentação. Termos técnicos consagrados (token, hash, router) ficam como são.
- **Segurança:** nenhuma credencial no código ou no Git; tudo pelo `.env` (ver `.env.example`). Nada de dados reais de clientes no repositório.
- **Testes:** todo comportamento novo vem com teste (`api/tests/` ou `web/tests/`). Rode `pytest` em `api/` e `npm test` em `web/` antes de cada commit. Os testes usam SQLite em memória, ou o PostgreSQL se `PIKI_TESTE_DATABASE_URL` estiver definido.
- **Roteiro:** ao concluir ou começar um item, atualize `docs/roteiro.md` no mesmo commit (`[x]` com a data, `[~]` em andamento).
- **Commits:** mensagem em português, primeira linha curta dizendo o que muda, corpo com os pontos principais.

## Comandos

```bash
docker compose up -d                 # PostgreSQL de desenvolvimento
cd api
pip install -e ".[dev]"
alembic upgrade head                 # aplica as migrações
pytest                               # testes
uvicorn app.main:app --reload        # API em http://localhost:8000/docs
python -m app.cli --help             # empresas, perfis, usuários, acessos
cd ../web
npm install && npm run dev           # front em http://localhost:9000
npm test
```

## Trabalho em paralelo

O Alison trabalha no VS Code e o Claude também envia mudanças direto para o GitHub. Faça `git pull` antes de começar e commits pequenos e frequentes, para evitar conflitos.
