# Decisões de arquitetura

Registro curto das decisões tomadas e do que ainda está em aberto. Quando uma decisão mudar, atualize o item e anote a data.

## Tomadas

### D1. Repositório separado do legado (30/10/2026)

O VB6 continua em `alisoncf/piki_vb`, intacto. O sistema novo começa aqui, com histórico limpo. O legado tem senhas, logs e dumps no histórico, e o `piki_Simples.vbp` depende de caminhos relativos entre pastas que não podem ser reorganizadas.

### D2. Stack: FastAPI + Vue/Quasar sobre o banco atual (30/10/2026)

A API lê e grava no mesmo MariaDB do VB6. A migração é por tela, não por big bang.

### D3. Filial na chave das tabelas de movimento (30/10/2026)

Tabelas de movimento (vendas, caixa, documentos, cheques, consignações, compras, estoque, NF-e, SPED) ganham `cod_emp CHAR(2)` como primeira coluna da chave primária, por exemplo `(cod_emp, num_ven)`. Cada filial continua numerando como hoje, e as bases podem ser juntadas sem renumerar nada.

Cadastros (clientes, fornecedores, produtos, seções etc.) passam a ser globais, com tabelas de mapeamento `map_*` do código antigo de cada filial para o código unificado. `tab_produtos` é separada em cadastro global e `produto_filial` (estoque, preço e custo por filial).

A classificação de cada tabela está na coluna `escopo_proposto` de `docs/legado/tabelas.csv`.

### D4. Coexistência: VB6 com banco local, sistema novo no central (30/10/2026)

As consultas do VB6 não filtram por `cod_emp`. Enquanto o VB6 estiver em uso numa filial, ele continua com o banco local, e o banco central é alimentado por sincronização, ampliando o mecanismo que já existe (módulo `API`, tabela `fila_transferencia`, `tab_doc.id_doc_web`).

### D5. Fiscal continua no ACBrMonitor PLUS (30/10/2026)

NF-e e NFC-e já são emitidas pelo ACBrMonitor. A API nova envia os mesmos comandos (por TCP, em vez de `ent.txt`/`sai.txt`) e não reimplementa a comunicação com a SEFAZ.

### D6. Pré-requisitos do banco único (30/10/2026)

Antes de consolidar: converter as tabelas de MyISAM para InnoDB, criar chave primária nas 48 tabelas que não têm, e usar `DECIMAL` no lugar de `double` para valores.

### D7. Login com migração das senhas para hash (30/10/2026)

O VB6 guarda as senhas em `tab_usuarios.SENHA_USU` com uma codificação reversível (`F_GeraPW`/`F_RetornaPW`), que qualquer pessoa com acesso ao banco consegue desfazer. O sistema novo tem sua própria tabela, `web_credencial`, com a senha guardada como hash argon2 e ligada ao `COD_FUN`.

No primeiro login de cada usuário no sistema novo, a API confere a senha no formato antigo e, se estiver certa, grava o hash. A tabela também guarda uma impressão digital (sha256) do `SENHA_USU` daquele momento: se a senha for trocada no VB6, o hash é refeito no login seguinte. Ninguém precisa recadastrar senha, e o VB6 continua funcionando igual.

Como no VB6, a senha não diferencia maiúsculas de minúsculas, e o usuário entra pelo apelido (`guerra_fun`) ou pelo código do funcionário. O login devolve um token (JWT) válido por 10 horas, que carrega o funcionário e a filial (`cod_emp`).

## Em aberto

- **P1.** O servidor da API web que o VB6 já usa (`desktop_doc`, `desktop_clientes`, `desktop_baixa`): qual a stack e onde está? Pode ser aproveitado ou absorvido pelo `piki-web`.
- **P2.** Cada filial já tem um `cod_emp` único no seu `tab_parametros`? Os registros já gravados estão com o `cod_emp` correto?
- **P3.** Clientes e produtos são do grupo todo ou de cada loja? Um cliente que compra em duas filiais deve ser o mesmo cadastro?
- **P4.** As lojas ainda usam ECF, ou só NFC-e? Se só NFC-e, o código e as tabelas de ECF são descartados.
- **P5.** ~~Formato do login~~ Resolvido na D7.
- **P6.** O login do VB6 monta o SQL concatenando o texto digitado (`frmLogin`), o que permite injeção de SQL. Vale corrigir no legado enquanto ele estiver em uso, já que basta trocar por uma consulta parametrizada.
