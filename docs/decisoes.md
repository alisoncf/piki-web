# Decisões de arquitetura

Registro curto das decisões tomadas e do que ainda está em aberto. Quando uma decisão mudar, não apague: marque como substituída, diga por qual e anote a data. O histórico explica por que o código está como está.

## Vigentes

### D1. Repositório separado do legado (30/10/2026)

O VB6 continua em `alisoncf/piki_vb`, intacto. O sistema novo começa aqui, com histórico limpo. O legado tem senhas, logs e dumps no histórico, e o `piki_Simples.vbp` depende de caminhos relativos entre pastas que não podem ser reorganizadas.

### D5. Fiscal continua no ACBrMonitor PLUS (30/10/2026)

NF-e e NFC-e já são emitidas pelo ACBrMonitor. A API nova envia os mesmos comandos (por TCP, em vez de `ent.txt`/`sai.txt`) e não reimplementa a comunicação com a SEFAZ.

### D8. Esquema novo, alimentado por ETL a partir das filiais (30/10/2026)

O sistema novo tem banco e esquema próprios, desenhados para várias empresas desde o começo: InnoDB/transações, chaves estrangeiras, `DECIMAL` para valores, nomes claros. Não herdamos a estrutura do VB6.

Cada filial tem hoje seu próprio banco local. Os dados chegam ao banco novo assim:

1. **Agente em cada filial:** programa pequeno que faz o dump do banco local e envia para o servidor central por HTTPS (só conexão de saída, sem abrir porta na loja).
2. **Área de chegada:** cada dump é carregado como está, num esquema separado por filial (`legado_f01`, `legado_f02`...).
3. **ETL:** lê cada área de chegada e grava no esquema novo, deduplicando cadastros e mapeando (empresa, código antigo) → id novo. É repetível: rodar de novo atualiza o que existe e insere o que é novo.

Enquanto o VB6 estiver em uso, ele é o sistema oficial e o ETL roda todo dia, em mão única. O sistema novo já serve para consultas e relatórios consolidados. A virada é por filial: quando as telas que uma filial usa estiverem prontas, ela passa a gravar no sistema novo e deixa de enviar dumps.

As senhas antigas são reversíveis (`F_GeraPW`/`F_RetornaPW`), então o ETL as converte para hash argon2 na importação. A conferência de senha no formato antigo existe só no ETL (`api/etl/senha_legado.py`), nunca na API.

### D9. Escopo dos dados entre empresas (30/10/2026)

Cada filial é uma **empresa** (CNPJ próprio). Os dados se dividem em três escopos:

| Escopo | Exemplos | Regra |
|---|---|---|
| Global | clientes, produtos (cadastro), fornecedores, seções, formas de pagamento | Um cadastro só, visível em todas as empresas |
| Por empresa | estoque, preço e custo do produto, notas fiscais de entrada e saída, vendas, caixa, inventário | Cada registro pertence a uma empresa; só aparece nela |
| Por empresa, visível em todas | contas a receber (documentos e parcelas) | O documento pertence à empresa que vendeu, mas pode ser consultado e recebido em qualquer empresa. A baixa registra em qual empresa e em qual caixa o dinheiro entrou |

Na prática: o cliente pode pagar o boleto ou a parcela em qualquer loja, e o caixa de quem recebeu é que registra a entrada.

### D10. Acesso: usuário, empresa e perfil (30/10/2026)

- Um **usuário** pode ter acesso a uma ou várias empresas. A relação usuário–empresa diz também **o que ele pode fazer ali**, por meio de um **perfil** (conjunto de permissões, por exemplo "Caixa", "Gerente", "Financeiro").
- O mesmo usuário pode ter perfis diferentes em empresas diferentes (gerente na 01, só consulta na 02).
- No login, o usuário escolhe a empresa. Se só tem acesso a uma, ela é escolhida automaticamente. Ele pode **trocar de empresa** a qualquer momento sem sair do sistema.
- O token de login carrega o usuário e a empresa ativa. As permissões são conferidas no banco a cada requisição, então uma permissão retirada vale na hora.
- Usuário marcado como administrador tem acesso total a todas as empresas.
- As permissões são códigos no formato `area.acao` (por exemplo `clientes.editar`, `caixa.abrir`), definidos no código e cadastrados no banco.

### D11. Back-end organizado por domínio (30/10/2026)

Cada domínio (acesso, cadastros, financeiro...) tem sua pasta em `api/app/dominios/`, com:

- `modelos.py`: tabelas (SQLAlchemy)
- `esquemas.py`: formatos de entrada e saída da API (Pydantic)
- `repositorio.py`: consultas ao banco
- `servico.py`: regras de negócio, sem depender de HTTP
- `rotas.py`: endpoints, que só recebem, chamam o serviço e devolvem

O que é comum a todos (banco, segurança, dependências de login e empresa) fica em `api/app/nucleo/`. A estrutura do banco é versionada com Alembic (`api/alembic/`).

### D12. PostgreSQL no servidor central (30/10/2026)

O banco do sistema novo é PostgreSQL (16 ou mais recente). As filiais continuam com MariaDB enquanto o VB6 estiver em uso; o ETL lê do MariaDB e grava no PostgreSQL.

Motivos: *row-level security* para isolar as empresas no próprio banco (uma consulta que esqueça o filtro de empresa é barrada pelo banco), migrações de estrutura transacionais (uma migração que falha não deixa o banco pela metade), `INSERT ... ON CONFLICT` e consultas analíticas maduras para o ETL e os relatórios consolidados, e tipos rígidos que obrigam o ETL a tratar as datas `0000-00-00` e textos fora do tamanho do banco antigo.

Para desenvolver: `docker compose up -d` sobe o PostgreSQL com os bancos `piki` e `piki_teste`. Sem banco configurado, a API e os testes usam SQLite.

## Substituídas

- **D2.** ~~FastAPI + Vue/Quasar sobre o banco atual~~. A stack continua, mas o banco passou a ser novo. Substituída pela D8 em 30/10/2026.
- **D3.** ~~Filial na chave das tabelas do banco atual~~. Com esquema novo, as tabelas já nascem com a empresa. Substituída pelas D8 e D9 em 30/10/2026.
- **D4.** ~~VB6 e sistema novo no mesmo banco, com sincronização~~. Substituída pela D8 (ETL de mão única e virada por filial) em 30/10/2026.
- **D6.** ~~Converter o banco atual para InnoDB e criar chaves~~. Desnecessário com esquema novo. Substituída pela D8 em 30/10/2026.
- **D7.** ~~Login conferindo a senha do VB6 e migrando para hash no primeiro acesso~~. Com o ETL, as senhas são convertidas na importação. Substituída pela D8 em 30/10/2026.

## Em aberto

- **P1.** O servidor da API web que o VB6 já usa (`desktop_doc`, `desktop_clientes`, `desktop_baixa`): qual a stack e onde está? Pode virar o servidor central ou ser absorvido pelo `piki-web`.
- **P2.** Códigos das empresas (`sped_empresa.codigo`, o `cod_emp` do VB6). Conhecidos em 30/10/2026: **01** (matriz, banco `requinte`) e **03** (loja do Jundiaí, banco `requintebps`). Falta saber se existe a 02 e outras, e conferir se os registros já gravados em cada banco estão com o código certo. O ETL recusa importar quando o mesmo código aparece com CNPJs diferentes.
- **P3.** ~~Clientes e produtos globais ou por loja?~~ Resolvido na D9.
- **P4.** As lojas ainda usam ECF, ou só NFC-e? Se só NFC-e, o código e as tabelas de ECF são descartados.
- **P6.** O login do VB6 monta o SQL concatenando o texto digitado (`frmLogin`), o que permite injeção de SQL. Vale corrigir no legado enquanto ele estiver em uso.
- **P7.** ~~PostgreSQL ou MariaDB?~~ Resolvido na D12.
- **P8.** Infraestrutura das filiais: quantas são, se o computador do banco fica ligado e com internet, e o tamanho de cada banco. Define a frequência do agente.
- **P10.** Segredos fiscais por empresa: certificado digital A1 (`.pfx` e senha) e CSC da NFC-e (id e token). No VB6 ficam em texto puro na `sped_empresa`; o ETL não os lê. Proposta: os arquivos `.pfx` ficam no servidor, fora do repositório e do banco, e senhas e tokens ficam cifrados no banco com uma chave que só existe no `.env` do servidor (ou num cofre de segredos). Decidir antes da onda 6.
- **P9.** Durante a transição, produtos cadastrados no sistema novo precisam chegar aos VB6 das filiais que ainda não viraram? Se o cadastro de produtos é feito por uma só pessoa ou pela matriz, pode ser preciso uma sincronização de volta só para produtos.
