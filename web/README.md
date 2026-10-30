# web

Front-end do Piki: Vue 3, Quasar, Pinia e Vue Router, com Vite.

```bash
npm install
npm run dev       # http://localhost:9000 (a API precisa estar rodando na 8000)
npm test          # testes (Vitest)
npm run build     # gera dist/ para produção
```

O front chama a API em `/api/...`; em desenvolvimento o Vite repassa para `http://localhost:8000` (mude com a variável `PIKI_API_URL`).

## Organização

```
src/
  main.js               liga Vue, Quasar, Pinia e o roteador
  router/index.js       rotas e regras de navegação (login, escolha de empresa, permissão)
  stores/sessao.js      usuário, empresa ativa, empresas e permissões
  servicos/api.js       cliente HTTP com o token e o tratamento de erros
  menu.js               itens do menu e a permissão que cada um exige
  layouts/              layout principal (barra com a troca de empresa e o menu lateral)
  paginas/              uma tela por arquivo, agrupadas por domínio (paginas/acesso/...)
  componentes/          peças reaproveitadas (marca da loja, assinatura do Piki)
  marca.js              nome e logos da loja e do sistema (arquivos em public/)
  css/quasar.variables.sass   cores da identidade visual (D14); tons de apoio em css/app.css
tests/
```

## Tela nova

1. Crie a página em `src/paginas/<dominio>/NomePagina.vue`.
2. Registre a rota em `src/router/index.js`, com `meta: { permissao: 'area.acao' }`.
3. Acrescente o item em `src/menu.js`, com a mesma permissão.

A permissão é o mesmo código da API (`api/app/nucleo/permissoes.py`). O front só esconde o que o usuário não pode usar; quem garante é a API.
