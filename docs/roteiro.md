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
- [x] Mapa das 279 tabelas do banco antigo, a partir do schema real — 30/10/2026
- [x] Criar o repositório `piki-web`, separado do legado — 30/10/2026
- [x] Decidir: esquema novo alimentado por ETL, escopo dos dados entre empresas, acesso por usuário–empresa–perfil (D8, D9, D10) — 30/10/2026
- [ ] Tornar o repositório `piki_vb` privado e trocar as senhas que estão expostas nele
- [ ] Responder as pendências P1, P2, P4, P8 e P9 de `decisoes.md`
- [ ] Corrigir a injeção de SQL no login do VB6 (P6)

## Onda 0 · Fundação

- [x] Esqueleto da API (FastAPI, configuração por `.env`) — 30/10/2026
- [x] `GET /saude`, com testes — 30/10/2026
- [x] Roteiro do projeto (este arquivo) — 30/10/2026
- [x] `CLAUDE.md` com o guia do projeto e as convenções — 30/10/2026
- [x] API organizada por domínio (`nucleo/` + `dominios/`), migrações com Alembic (D11) — 30/10/2026
- [x] Tabelas de acesso: empresa, usuário, perfil, permissão, usuário–empresa (migração 0001) — 30/10/2026
- [x] Login com escolha da empresa, troca de empresa sem sair (`POST /auth/login`, `POST /auth/empresa`, `GET /auth/eu`) — 30/10/2026
- [x] Permissões por empresa, conferidas a cada requisição (`exige("area.acao")`) — 30/10/2026
- [x] Comandos de administração (`python -m app.cli`): empresas, perfis, usuários, acessos — 30/10/2026
- [x] Banco: PostgreSQL (D12), com `docker-compose.yml` para desenvolvimento; migração 0001 e testes validados no PostgreSQL 16 — 30/10/2026
- [ ] Ativar o isolamento por empresa no banco (*row-level security*) junto com a primeira tabela por empresa
- [x] Telas de administração: cadastro de usuários, perfis e acessos (API + web), com as regras do gerente da loja (D23) — 02/11/2026
- [x] Senha provisória e troca de senha pelo próprio usuário (desliga o modo "sem diferenciar maiúsculas" das senhas importadas) — 02/11/2026
- [x] Bloqueio do login na quinta senha errada, por 15 minutos (migração 0015) — 02/11/2026
- [ ] Recuperação de senha por e-mail
- [ ] Autenticação em dois fatores (pelo menos para administradores e gerentes)
- [x] Front-end `web/` (Vue 3 + Quasar + Pinia, D13): login, escolha e troca de empresa, menu conforme as permissões, lista de usuários — 30/10/2026
- [x] Identidade visual: marca da Requinte Enxovais, ícone do Piki, cores e fonte (D14) — 30/10/2026
- [x] Cor de identificação por empresa: faixa, selo, menu e aba do navegador (migração 0003) — 30/10/2026
- [ ] Testar o front no navegador com usuários reais
- [ ] Decidir onde guardar o token no navegador antes de produção (P11)
- [ ] Definir onde a API vai rodar (servidor, domínio, HTTPS) e o processo de deploy

## Dados das filiais: agente e ETL (transversal)

Decisão D8. Pode avançar em paralelo com as ondas 1 e 2. Detalhes em [`../api/etl/README.md`](../api/etl/README.md).

- [x] Conversão das senhas do VB6 para hash (`etl/senha_legado.py`) — 30/10/2026
- [ ] Levantar a infraestrutura das filiais: quantas, computador do banco, internet, tamanho (P8)
- [~] Confirmar o código de cada empresa (P2): conhecidos 01 e 03
- [x] Cadastro de empresa com dados fiscais e endereço (migração 0002) — 30/10/2026
- [x] ETL de empresas a partir da `sped_empresa`, sem ler certificado nem CSC (`python -m etl empresas`) — 30/10/2026
- [x] Rodar o ETL de empresas nos bancos da matriz (01) e da La Viva (03), em cópias locais — 30/10/2026
- [~] Rodar o ETL nas cópias dos bancos das outras filiais: Jundiaí Casa (02, banco `requintejun`) feita em 30/10/2026; faltam as demais
- [ ] Decidir onde guardar certificado digital e CSC de cada empresa (P10)
- [ ] Agente da filial: dump do banco local e envio por HTTPS
- [ ] Recebimento no servidor e carga na área de chegada (`legado_fXX`)
- [x] ETL de usuários, com a conversão de senhas e os perfis a partir do nível do VB6 (D23), rodado nas três cópias — 02/11/2026
- [x] ETL de clientes, deduplicados por CPF/CNPJ, com setores, órgãos e grupos unificados (D15) — 30/10/2026
- [x] ETL de produtos, seções e subseções, do banco da matriz (D24) — 02/11/2026
- [ ] Depois de importar vendas e contas: excluir os clientes sem CPF/CNPJ válido que não têm movimento (D15)
- [ ] ETL dos demais domínios, acompanhando as ondas
- [ ] Decidir se produtos cadastrados no sistema novo voltam para os VB6 durante a transição (P9)

## Onda 1 · Cadastros

- [x] Clientes, setores, órgãos, grupos e parentescos (D15): API (migrações 0006 e 0007), telas (lista paginada pela API, ficha com telefones, referências e anotações, setores com cobrador por loja, órgãos, grupos, parentescos) e ETL, rodado nas cópias da matriz, Jundiaí e La Viva (80 mil clientes) — 30/10/2026
- [x] Fornecedores (D22): API (migração 0014), lista, ficha em página única com contatos e busca do CNPJ na BrasilAPI, e ETL rodado nas cópias da matriz, Jundiaí e La Viva (267 fornecedores) — 02/11/2026
- [x] Funcionários e cargos: API, telas (lista, ficha, cargos) e ETL do VB6, com cadastro global, loja de lotação e telefones (migrações 0004 e 0005) — 30/10/2026
- [x] Rodar o ETL de funcionários nos bancos da matriz (01) e da La Viva (03), em cópias locais, juntando os cadastros repetidos entre filiais (pelo CPF ou pelo nome) — 30/10/2026
- [x] Usuários ligados a funcionários (D23) — 02/11/2026
- [x] Cidades do IBGE e cobradores (D16, D17): setor escolhe a cidade numa lista e tem vários cobradores, que são funcionários e valem para todas as lojas; o cliente não tem cidade própria, usa a do setor; migrações 0008 e 0009 e ETL refeito nas três cópias — 31/10/2026
- [x] Funcionário com setor no endereço, no lugar de bairro, cidade e UF digitados; cliente sem o campo bairro (D17, migração 0010) — 31/10/2026
- [x] Endereço pelo CEP (ViaCEP) nas fichas de cliente e funcionário, com o setor adivinhado pelo bairro ou cadastrado na hora (D18) — 31/10/2026
- [x] Atalhos da tela inicial para as telas dos subgrupos do menu; fundo das telas no tom da empresa ativa — 31/10/2026
- [x] Cadastro de empresas (D19): lista e ficha com dados fiscais, endereço com cidade do IBGE e busca pelo CEP, esquema de cores (principal, fundo e menu) aplicado ao entrar na empresa, logo e QR code do boleto; migração 0011 — 01/11/2026
- [x] Documentos digitais do cliente para o crediário (D20): envio de arquivo ou foto, permissão própria pela LGPD, arquivos numa pasta do servidor ou no MinIO; migração 0013 — 01/11/2026
- [x] Clientes atualizados pelo `requinte`; sem CPF/CNPJ válido ou com nome sem sentido ficam de fora, menos quem tem dívida em aberto (D21) — 01/11/2026
- [x] Cadastro repetido com nome sem sentido não manda nos dados do cliente com o mesmo CPF (D21) — 02/11/2026
- [x] Ficha do cliente em página única com índice fixo das partes; menu lateral fixo ao rolar — 02/11/2026
- [ ] Nomes do VB6 hoje em maiúsculas (setores, clientes...) passarem para maiúsculas só nas iniciais; os cadastros novos já são gravados assim
- [ ] Bancos, formas de pagamento, plano de contas

## Onda 2 · Relatórios

Com o ETL rodando, os relatórios já podem mostrar todas as filiais juntas, antes de qualquer virada.

- [ ] Levantar quais relatórios são realmente usados e priorizar
- [ ] Padrão de relatório na web (filtros, PDF, Excel)
- [ ] Migrar os relatórios por ordem de uso

## Onda 3 · Financeiro

- [~] Contas a pagar e a receber (`tab_doc`, `tab_itdoc`): o carnê do crediário gera a conta a receber, e o ETL das contas a receber de clientes rodou nas três cópias (D26, migração 0025) — 02/11/2026; faltam as operações do contas a receber (cobrança em lote, baixa de vários carnês), os representantes e as contas a pagar
- [x] Baixa de parcelas em qualquer empresa, registrando o caixa de quem recebeu (D9, D26): juros de atraso sugeridos por dia, pagamento parcial, várias formas, estorno (migração 0024) — 02/11/2026
- [~] Tela de contas a receber (D26): filtros, somas, seleção e baixa das selecionadas com distribuição do valor (migração 0026) — 02/11/2026; faltam a cobrança (conta e tipo), o desconto na baixa e as outras operações do VB6
- [x] Prejuízo da parcela (D26): pôr e tirar com o motivo, fora da lista, conta no limite; ETL pela marca e pela conta de cobrança PREJUIZO (migração 0027) — 03/11/2026
- [ ] Cheques
- [ ] Cobrança e carnês
- [ ] Testes comparando os resultados do sistema novo com os do VB6

## Onda 4 · Estoque e compras

- [x] Cadastro de produtos (D24): API (migração 0016), lista paginada pela API, ficha com códigos de barras, fornecedores e fotos, seções e marcas — 02/11/2026
- [x] Estoque por loja (D24): quantidade, reservado, localização e impostos da empresa, ajuste com motivo e histórico de movimentos, na ficha do produto (migração 0017); ETL do saldo do VB6 rodado nas três cópias — 02/11/2026
- [ ] Saldo inicial do estoque: inventário de 31/12/2025 + notas de saída e entradas desde então
- [x] Entrada de notas pelo XML (D25): carga, ligação dos itens (com atalho para cadastrar o produto), embalagem, custo, preço e entrada no estoque (migração 0018) — 02/11/2026
- [ ] Conferir a entrada com XMLs reais dos fornecedores
- [ ] Buscar as notas de entrada na SEFAZ (distribuição de DF-e, com o certificado)
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

- [x] Formato do PDV: web, imprimindo pela janela do navegador (D26); o TEF decide se vai precisar de um agente local — 02/11/2026
- [ ] NFC-e e canhoto de retirada
- [ ] TEF (SiTef)
- [x] Formas de pagamento e caixa (D26): caixas da loja, abertura com fundo de troco, entradas e saídas, fechamento com conferência cega (migração 0019); ETL das formas e caixas rodado nas três cópias — 02/11/2026
- [x] Venda (D26): vendedor monta, caixa recebe, desconto pela forma com limite do perfil e autorização, venda aberta vence em 10 dias (migração 0020) — 02/11/2026
- [x] Crediário na venda (D26): limite do cliente somando todas as lojas, entrada, parcelas sem juros e carnê pela janela de impressão (migração 0021) — 02/11/2026
- [x] Ajustes da venda (D26): o vendedor fecha e o caixa recebe a fechada, venda a consumidor com cadastro curto, entrega com taxa e endereço, produto em queima sem desconto (migração 0022) — 02/11/2026
- [x] Recebimento no caixa (D26): o computador fica no caixa, troca da forma no caixa, pagamento em várias formas, data base do crediário, escolha NFC-e ou NF-e (migração 0023) — 02/11/2026
- [ ] Trocas, cancelamento, entrega, cartão presente
- [ ] Controle de vales por funcionário
- [ ] Conciliação do cartão pelo extrato da financeira
- [ ] Importação do histórico de vendas do VB6
- [ ] Operação offline com sincronização

## Virada das filiais

- [ ] Escolher a filial piloto
- [ ] Todas as telas que ela usa prontas no sistema novo
- [ ] Última importação pelo ETL, e a filial passa a gravar só no sistema novo
- [ ] Repetir para cada filial
- [ ] Desligar o VB6
