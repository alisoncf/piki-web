# Inventário do legado: piki_Simples (VB6 + MySQL)

Levantamento do projeto `requinte/prj/piki_Simples.vbp` (executável `Piki_2018.exe`) no repositório `alisoncf/piki_vb`, branch `main`, e do schema do banco `requinte` (MariaDB 11.6), em 30/10/2026. Serve de mapa para a migração gradual para FastAPI + Vue/Quasar e para a integração das filiais num banco único.

Arquivos desta pasta:

- `README.md`: este resumo, com a ordem de migração e a proposta para as filiais (seção 7).
- `inventario.csv`: uma linha por form, módulo ou classe do projeto, com domínio, onda, tabelas, integrações e colunas para acompanhar a migração (`status_migracao`, `destino_novo`, `observacoes`).
- `tabelas.csv`: uma linha por tabela (as 279 do banco e as que o código cita mas não existem), com engine, chave primária, se já tem `cod_emp`, quem lê e escreve, e o escopo proposto para o banco único.

## 1. Tamanho real

| Item | Valor |
|---|---|
| Itens no projeto | 416 (314 forms, 101 módulos, 1 classe) |
| Linhas de código (sem o designer dos forms e sem comentários) | ~98 mil |
| Linhas totais dos arquivos (incluindo o layout das telas) | ~246 mil |
| Tabelas citadas no SQL | ~250 |
| Itens sem nenhuma referência no código | 58 (11 deles vazios) |

O volume é bem menor do que o repositório inteiro sugere (~770 mil linhas). A maior parte do repositório são outros projetos e cópias.

De onde vêm os arquivos que entram no build:

| Pasta | Itens |
|---|---|
| `requinte/` | 354 |
| `modulo nfe/` | 44 (todo o NF-e/NFC-e, ACBr, TEF, QR Code) |
| `piki Sped/` | 10 |
| `sped/` | 8 (entrada de notas e participantes do SPED) |

## 2. Mapa por domínio

| Onda | Domínio | Forms | Módulos | Linhas de código | Itens principais |
|---|---|---|---|---|---|
| 0 | Núcleo / infraestrutura | 10 | 7 | 6.854 | `Modulo`, `BancoDados`, `mdiFrm`, `frmLogin`, `frmMenu` |
| 1 | Cadastros | 47 | 12 | 8.047 | `frmCadCli`, `Clientes`, `frmCadFun`, `frmEdiClientes` |
| 2 | Relatórios | 43 | 2 | 10.459 | `Relatorios`, `frmRelComiss`, `frmRelVendasVendedor`, `frmRelProdLucr` |
| 3 | Financeiro (pagar/receber, cheques, cobrança) | 55 | 9 | 13.984 | `doc`, `frmEditaMov`, `frmBaixaDocReq`, `frmCobranca` |
| 4 | Estoque / Compras | 50 | 12 | 12.526 | `frmEntradas`, `Produtos`, `frmCadPro`, `frmEdiPro` |
| 5 | Consignação / Representantes | 21 | 4 | 8.221 | `frmAcerto`, `frmCadRep`, `frmTransfConsign`, `frmConsign` |
| 6 | Fiscal: NF-e / NFC-e | 15 | 15 | 8.951 | `NFe`, `AcBrMonitor`, `NFEUtil`, `frmNFE_Detalhe` |
| 6 | Fiscal: SPED / entrada de notas | 11 | 6 | 6.376 | `frmEntradaSped`, `SpedNF`, `frmSpedImportarXMLNF` |
| 7 | PDV / Caixa | 43 | 11 | 14.707 | `frmTroco`, `tef_nfe`, `frmVenda`, `frmVendaFunc` |
| — | Descartar: ECF / legado fiscal | 3 | 7 | 2.993 | `ImpressoraECF`, `ECF`, `daruma`, `Elgin`, `BemaFi32`, `Sintegra` |
| — | Utilitários / helpers VB6 | 16 | 17 | 5.150 | `API`, `html`, `HTTPUtil`, `JSONUtil`, telas de migração e teste |

A classificação foi feita pelo nome e conteúdo de cada item, com alguns ajustes manuais. Vale revisar a coluna `dominio` do `inventario.csv` antes de começar cada onda.

## 3. Ordem de migração proposta

A lógica é começar pelo que tem menos risco e não depende de hardware, e deixar para o fim o que fica no balcão da loja.

**Onda 0: Fundação.** Projeto novo (`api/` FastAPI e `web/` Vue/Quasar), conexão com o MySQL atual, login usando `tab_usuarios` e as permissões de `tab_permissoes`/`tab_permgru`, e o equivalente ao menu principal. Nenhuma tela do legado é desligada nesta onda.

**Onda 1: Cadastros.** Clientes, fornecedores, funcionários, cidades, setores, órgãos, cargos, usuários. São telas de CRUD, com pouca regra de negócio, e servem para estabilizar o padrão de API e de tela que as outras ondas vão repetir. Atenção: `tab_telefones` é escrita por cadastros de clientes, fornecedores, funcionários e representantes.

**Onda 2: Relatórios.** Só leem dados, então não há risco de corromper nada. É também onde a web traz ganho visível (filtros, exportação para PDF/Excel, acesso fora da loja). O módulo `Relatorios` (2,7 mil linhas) concentra a maior parte da lógica.

**Onda 3: Financeiro.** Contas a pagar e receber (`tab_doc`, `tab_itdoc`), cheques, cobrança, carnês, plano de contas. É o primeiro domínio que escreve em tabelas compartilhadas, então convém ter testes comparando o resultado do sistema novo com o antigo.

**Onda 4: Estoque e Compras.** Produtos, entradas, inventário, contagens, perdas, movimento interno, etiquetas. `tab_produtos` é a tabela mais usada do sistema (57 itens), e o cadastro de produto tem regras fiscais (CST, NCM) ligadas ao SPED e à NF-e.

**Onda 5: Consignação e Representantes.** Consignações, devoluções e acertos. É um fluxo próprio do negócio e com muita regra: `frmAcerto` sozinho tem 2 mil linhas. Depende do financeiro e do estoque já migrados.

**Onda 6: Fiscal.** Entrada de notas e SPED, emissão de NF-e e NFC-e. Ver a seção 4 sobre o ACBrMonitor, que simplifica bastante esta onda.

**Onda 7: PDV e Caixa.** Venda, troco, TEF, abertura e fechamento de caixa, trocas, vales, cartão presente. Fica por último porque depende de impressora, TEF e leitor no computador do caixa. Pode virar um app desktop ou uma tela web com um agente local para o hardware.

**Não migra.** O código de ECF (Bematech, Daruma, Elgin) e o Sintegra, se não estiverem mais em uso, e os helpers do VB6 (HTTP, JSON, XML, PDF, ZIP, grids), que são substituídos por bibliotecas da stack nova.

## 4. Pontos de atenção

**NF-e e NFC-e passam pelo ACBrMonitor PLUS.** O módulo `AcBrMonitor` grava comandos em `C:\ACBrMonitorPLUS\ent.txt` e lê a resposta em `sai.txt` (por exemplo `NFe.CriarEnviarNFe`, `NFe.ImprimirDANFE`). Isso é uma boa notícia: o backend novo pode continuar usando o mesmo ACBrMonitor, que também aceita comandos por TCP, em vez de reimplementar a comunicação com a SEFAZ. O trabalho da onda 6 passa a ser montar o INI da nota a partir do banco, o que hoje está em `NFe`, `NFe_DAO` e `XML_NFE`.

**O código de ECF ainda está no build.** São ~3 mil linhas e 15 itens com chamadas às DLLs de impressora fiscal. Se as lojas já emitem só NFC-e, esse código pode ser removido e não precisa ser migrado. Confirmar antes da onda 7.

**O schema real.** O `tabelas.sql` do repositório está desatualizado (119 tabelas). O dump do banco de produção tem 279 tabelas, das quais 204 são usadas pelo piki_Simples. O código cita outras 46 que não existem neste banco (por exemplo `tab_lojas`, `tab_estoque`, `tab_transferencias`, `tab_cupons`): são caminhos de código de outras variantes ou tabelas criadas em tempo de execução, e não devem ir para os modelos da API sem conferência. Não há procedures, triggers, views nem chaves estrangeiras: toda a integridade está no código VB6.

**MyISAM.** 273 das 279 tabelas são MyISAM, que não tem transações nem chaves estrangeiras. Uma venda que grava em `tab_vendas`, `tab_itvendas`, `tab_caixa` e `tab_doc` pode ficar pela metade se algo falhar no meio. A conversão para InnoDB é pré-requisito para o banco único (seção 7).

**Valores em `double`.** Preços, custos e valores financeiros são `double(14,2)`, que acumula erro de arredondamento. No schema novo, usar `DECIMAL(14,2)`.

**Tabelas escritas por vários domínios.** Treze tabelas recebem escrita de três domínios ou mais: `tab_produtos`, `tab_vendas`, `tab_itvendas`, `tab_doc`, `tab_itdoc`, `tab_caixa`, `tab_cheques`, `tab_acertos`, `tab_estcons`, `tab_comissparc`, `tab_codbarras`, `tab_embalagens`, `tab_telefones`. Enquanto os dois sistemas convivem, essas são as tabelas em que o novo e o antigo precisam gravar exatamente do mesmo jeito. O `tabelas.csv` lista quem escreve em cada uma.

**Regra de negócio dentro das telas.** Quase todo o SQL está montado como texto dentro dos forms. A migração de cada tela começa por extrair essas consultas e regras para a API, não por redesenhar a tela.

**Data binding e DAO.** 24 itens usam `Adodc`/`DataSource` (a tela grava direto no banco ao editar o grid) e 4 ainda usam DAO. São os pontos em que a regra de gravação está menos visível no código.

**Código sem referência.** 58 itens não são citados por nenhum outro, e 11 estão vazios. São candidatos a código morto, mas alguns podem ser abertos de forma indireta (por nome em texto, por exemplo). A coluna `sem_referencia_no_codigo` marca esses itens para conferência.

**Cópias divergentes.** 246 dos 416 itens têm um arquivo de mesmo nome em outra pasta do repositório com conteúdo diferente. O build usa apenas os caminhos da coluna `arquivo`. Ao corrigir um bug no legado, conferir que a alteração está indo para esse arquivo.

**Segurança.** O repositório do legado é público e contém arquivos `piki.ini` com campos de senha, senhas fixas no código, logs e um dump SQL com dados de movimentação. Tornar o repositório privado e trocar as senhas. No sistema novo, credenciais só em `.env`, nunca no código.

## 5. Como usar o `inventario.csv`

Cada linha tem as colunas `status_migracao` (começa como `pendente`), `destino_novo` e `observacoes`. A sugestão é atualizar essas colunas a cada tela migrada, com valores como `pendente`, `em andamento`, `em produção no novo`, `desligado no legado`, `descartado`. Em `destino_novo`, anotar a rota da tela e os endpoints que a substituem. Assim o CSV vira o painel de acompanhamento da migração.

## 6. Como foi gerado e limitações

O levantamento foi feito por script, lendo o `.vbp` e cada arquivo referenciado. As tabelas foram extraídas do SQL por expressões regulares sobre o código, então podem aparecer nomes a mais ou faltar tabelas montadas dinamicamente. As integrações (`ecf`, `nfe`, `tef` etc.) indicam menção no código, não uso confirmado em produção. A detecção de "sem referência" procura o nome do form no código dos outros itens. Os números servem para planejar e estimar, não substituem a leitura de cada tela no momento da migração.

## 7. Integração das filiais num banco único

> **Atualização (30/10/2026):** esta seção descreve a primeira proposta, de adaptar o banco atual. Ela foi substituída pelas decisões D8 a D10 em `docs/decisoes.md`: o sistema novo tem esquema próprio, alimentado por ETL. A análise abaixo continua útil como mapa do que o ETL precisa resolver (códigos repetidos entre filiais, estoque dentro de `tab_produtos`, tabelas sem chave).

Hoje cada filial tem seu próprio banco `requinte`, e os códigos (clientes, vendas, documentos, produtos) são gerados em cada uma com `max()+1` ou sequências próprias. Ao juntar as bases, o mesmo número aparece em várias filiais significando coisas diferentes. A proposta abaixo resolve isso com o mínimo de mudança na lógica que já existe.

### 7.1 O que já existe

- **`cod_emp` já está em 13 tabelas**: `tab_vendas`, `tab_itvendas`, `nfe`, `nfe_item`, `sped_nf`, `inventario`, `inventario_it`, `contagem`, `tab_parametros` e as tabelas de parcelas e quitação usadas pela integração web. A tabela `tab_parametros` tem `cod_emp`, `cod_loj` e `CNPJ_EMP`.
- **Já há uma integração com um servidor web.** O módulo `API` envia documentos, parcelas, baixas, clientes e seções para uma API (`desktop_doc`, `desktop_clientes`, `desktop_baixa`, `desktop_secao`), sempre passando `cod_emp`. A tabela `fila_transferencia` (InnoDB) é a fila dessa sincronização, e `tab_doc.id_doc_web` guarda o id do documento no servidor. Ou seja, o padrão "código local + filial ↔ id central" já está em uso.

### 7.2 Três tipos de tabela

A coluna `escopo_proposto` do `tabelas.csv` classifica cada tabela. Resumo das 279 do banco:

| Escopo | Tabelas | Em uso | O que muda |
|---|---|---|---|
| Por filial | 164 | 128 | Ganha `cod_emp`, que entra na chave primária |
| Global | 82 | 60 | Uma única cópia para todas as filiais; os códigos são unificados na consolidação |
| Configuração da filial | 7 | 6 | Uma linha (ou um conjunto) por filial, chave `cod_emp` |
| Global + dados por filial | 1 | 1 | `tab_produtos`: separar em duas tabelas |
| Descartar (ECF, backups, temporárias) | 16 | 3 | Não vão para o banco único |
| Verificar | 9 | 6 | Classificar manualmente |

A classificação é uma proposta feita pelo nome e uso de cada tabela. Os casos discutíveis (por exemplo, se funcionários e representantes são do grupo todo ou de cada loja, ou se `tab_contacob` é cadastro ou movimento) dependem de como o negócio funciona e devem ser decididos antes da onda 0.

### 7.3 Regras propostas

**Tabelas por filial: `cod_emp` na chave.** Toda tabela de movimento (vendas, caixa, documentos, cheques, consignações, compras, estoque, NF-e, SPED) recebe `cod_emp`, inclusive as tabelas de itens, e a chave primária passa a ser composta:

```sql
ALTER TABLE tab_vendas ENGINE=InnoDB;
-- tab_vendas já tem cod_emp; nas demais, adicionar antes:
-- ALTER TABLE tab_itvendas ADD cod_emp CHAR(2) NOT NULL DEFAULT '01' FIRST;
ALTER TABLE tab_vendas DROP PRIMARY KEY, ADD PRIMARY KEY (cod_emp, num_ven);
```

A vantagem é que a numeração atual continua valendo: cada filial segue gerando `num_ven`, `seq_doc` etc. como hoje, só que filtrando por `cod_emp`. Ao consolidar as bases, nenhum número precisa ser renumerado, porque a chave passa a ser (filial, número).

**Tabelas globais: unificar os códigos.** Clientes, fornecedores, produtos, seções e as demais tabelas de cadastro passam a existir uma vez só. Na consolidação, cada código local recebe um código central, e uma tabela de mapeamento guarda a correspondência para converter as tabelas por filial que apontam para ele:

```sql
CREATE TABLE map_cliente (
  cod_emp      CHAR(2) NOT NULL,
  cod_cli_old  INT     NOT NULL,
  cod_cli      INT     NOT NULL,   -- código no banco único
  PRIMARY KEY (cod_emp, cod_cli_old)
);
```

Clientes e fornecedores são deduplicados por CPF/CNPJ (`cpf_cli`, `CNPJ_FOR`). Produtos, por código de barras ou pelo próprio `cod_pro`, se as filiais já compartilham o mesmo cadastro.

**`tab_produtos`: separar cadastro de estoque e preço.** Hoje o estoque (`er_pro`, `ef_pro`), o preço de venda (`pv_pro`) e os custos (`cr_pro`, `cf_pro`, `cm_pro`) ficam na própria linha do produto. Com várias filiais, cada uma tem seu estoque e, possivelmente, seu preço:

```sql
CREATE TABLE produto_filial (
  cod_emp  CHAR(2)       NOT NULL,
  cod_pro  VARCHAR(8)    NOT NULL,
  estoque_real   DECIMAL(14,3) NOT NULL DEFAULT 0,
  estoque_fiscal DECIMAL(14,3) NOT NULL DEFAULT 0,
  preco_venda    DECIMAL(14,2) NOT NULL DEFAULT 0,
  custo_real     DECIMAL(14,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (cod_emp, cod_pro)
) ENGINE=InnoDB;
```

**Configuração da filial.** `tab_parametros` vira a tabela de filiais (uma linha por `cod_emp`, com CNPJ, IE e endereço). `sped_empresa`, `tab_caixas` e a numeração/série de NF-e e NFC-e ficam por filial, já que cada CNPJ tem sua própria numeração na SEFAZ.

### 7.4 Pré-requisitos e cuidados

- **Converter para InnoDB** antes de qualquer coisa. Sem transações, um banco único acessado por várias filiais ao mesmo tempo fica sujeito a gravações pela metade.
- **Criar chave primária nas 48 tabelas que não têm.** 32 delas estão em uso, quase todas do grupo `nfe_item_imposto_*`, `nfe_transp_*`, além de `tab_parametros`, `tab_telefones` e `tab_itperdas`.
- **Padronizar `cod_emp`.** O default é `'01'` em `tab_vendas` e `'02'` em `tab_parametros`. Antes de consolidar, confirmar que cada filial tem um `cod_emp` único e que ele está preenchido corretamente em todas as linhas já gravadas.
- **O VB6 e o banco único.** As consultas do legado não filtram por `cod_emp`. Se o VB6 de uma filial apontar para o banco único, ele vai ver (e alterar) dados das outras filiais. Por isso, enquanto o VB6 estiver em uso, cada filial continua com seu banco local, e o banco central é alimentado por sincronização, ampliando o mecanismo que já existe em `API` e `fila_transferencia`. Cada tela migrada para o sistema novo passa a ler e gravar direto no central.
- **PDV e internet.** Mesmo depois da migração, o caixa não deve parar se a internet cair. A retaguarda (cadastros, relatórios, financeiro) pode ser 100% central e web. O PDV deve continuar capaz de vender offline e sincronizar depois, como a própria NFC-e prevê com a emissão em contingência.
