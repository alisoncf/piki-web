# Roteiro do projeto

O caminho da migração: o que já foi feito e o que vem a seguir. Este arquivo é a referência para saber onde estamos. Atualize-o junto com cada commit que conclui ou muda um item.

Legenda: `[x]` feito · `[~]` em andamento · `[ ]` a fazer

Documentos relacionados:

- [`decisoes.md`](decisoes.md): o porquê das escolhas e as perguntas em aberto.
- [`legado/README.md`](legado/README.md): o inventário do VB6 e a lógica das ondas.
- [`legado/inventario.csv`](legado/inventario.csv): o acompanhamento tela a tela (colunas `status_migracao` e `destino_novo`).

---

## Preparação

- [x] Analisar o repositório do legado (`piki_vb`) e identificar o projeto em produção (`piki_Simples`) — 30/10/2026
- [x] Inventário do piki_Simples: 416 itens, ~98 mil linhas, classificados por domínio e onda — 30/10/2026
- [x] Mapa das 279 tabelas do banco a partir do schema real, com escopo proposto para o banco único — 30/10/2026
- [x] Criar o repositório `piki-web`, separado do legado — 30/10/2026
- [ ] Tornar o repositório `piki_vb` privado e trocar as senhas que estão expostas nele
- [ ] Responder as pendências P1 a P4 de `decisoes.md`
- [ ] Corrigir a injeção de SQL no login do VB6 (P6)

## Onda 0 · Fundação

- [x] Esqueleto da API (FastAPI, configuração por `.env`, conexão com o MariaDB) — 30/10/2026
- [x] Identificação da filial por requisição (`X-Cod-Emp`) — 30/10/2026
- [x] `GET /saude`, com testes — 30/10/2026
- [x] Roteiro do projeto (este arquivo) — 30/10/2026
- [x] Login com migração das senhas do legado para hash: `POST /auth/login`, `GET /auth/eu`, tabela `web_credencial` (decisão D7) — 30/10/2026
- [ ] Aplicar `api/migracoes/001_web_credencial.sql` numa cópia do banco e testar o login com usuários reais
- [ ] Permissões: ler `tab_permissoes`/`tab_permgru` e proteger as rotas por permissão
- [ ] Limitar tentativas de login (o VB6 bloqueia na 4ª tentativa)
- [ ] Criar o front-end `web/` (Vue 3 + Quasar): tela de login e menu principal
- [ ] Definir onde a API vai rodar (servidor, domínio, HTTPS) e o processo de deploy

## Banco único das filiais (transversal)

Pode começar em paralelo com as ondas 1 e 2. Detalhes na seção 7 de [`legado/README.md`](legado/README.md).

- [ ] Confirmar o `cod_emp` de cada filial e conferir os registros já gravados (P2)
- [ ] Decidir quais cadastros são globais e quais são por loja (P3)
- [ ] Converter as tabelas de MyISAM para InnoDB
- [ ] Criar chave primária nas 48 tabelas sem chave
- [ ] Adicionar `cod_emp` às tabelas de movimento e colocá-lo na chave primária
- [ ] Separar `tab_produtos` em cadastro global + `produto_filial`
- [ ] Script de consolidação: juntar as bases das filiais com as tabelas `map_*`
- [ ] Sincronização filial → central enquanto o VB6 estiver em uso (ampliar `fila_transferencia`)

## Onda 1 · Cadastros

- [ ] Clientes
- [ ] Fornecedores
- [ ] Funcionários e usuários
- [ ] Cidades, setores, órgãos, cargos
- [ ] Bancos, formas de pagamento, plano de contas

## Onda 2 · Relatórios

- [ ] Levantar quais relatórios são realmente usados e priorizar
- [ ] Padrão de relatório na web (filtros, PDF, Excel)
- [ ] Migrar os relatórios por ordem de uso

## Onda 3 · Financeiro

- [ ] Contas a pagar e a receber (`tab_doc`, `tab_itdoc`)
- [ ] Baixa de parcelas
- [ ] Cheques
- [ ] Cobrança e carnês
- [ ] Testes comparando os resultados do sistema novo com os do VB6

## Onda 4 · Estoque e compras

- [ ] Cadastro de produtos (com `produto_filial`)
- [ ] Entrada de notas e compras
- [ ] Inventário e contagens
- [ ] Perdas, movimento interno, etiquetas

## Onda 5 · Consignação e representantes

- [ ] Representantes
- [ ] Consignações e devoluções
- [ ] Acertos

## Onda 6 · Fiscal

- [ ] Comunicação com o ACBrMonitor PLUS por TCP
- [ ] Emissão de NF-e
- [ ] Entrada de notas e SPED
- [ ] Confirmar se o ECF ainda é usado; se não, remover do escopo (P4)

## Onda 7 · PDV e caixa

- [ ] Definir o formato do PDV: desktop ou web com agente local para impressora e TEF
- [ ] Venda, troco, NFC-e
- [ ] TEF (SiTef)
- [ ] Abertura e fechamento de caixa, trocas, vales, cartão presente
- [ ] Operação offline com sincronização

## Desligamento do VB6

- [ ] Todas as telas de uma filial em uso no sistema novo
- [ ] Filial passa a usar só o banco central
- [ ] Repetir para cada filial
