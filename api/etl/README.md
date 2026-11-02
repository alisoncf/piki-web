# ETL: do VB6 para o esquema novo

Decisão D8 em `docs/decisoes.md`. O caminho dos dados:

```
banco da filial (MariaDB local)
   │  agente: dump diário, enviado por HTTPS
   ▼
área de chegada no servidor: um esquema por filial (legado_f01, legado_f02...)
   │  ETL (esta pasta)
   ▼
banco novo (todas as empresas)
```

Regras gerais:

- **Repetível.** Rodar de novo atualiza o que já existe e insere o que é novo. Nada é duplicado.
- **Rastreável.** Cada registro importado guarda de onde veio (empresa e código antigo), numa tabela de mapeamento. É ela que permite reimportar e que liga, por exemplo, uma venda antiga ao cliente novo.
- **Escopo pela D9.** Cadastros globais são deduplicados entre filiais (clientes por CPF/CNPJ, produtos por código). Dados por empresa entram com a empresa de origem.

## Uso

```bash
pip install -e ".[legado]"     # driver para ler o MariaDB do VB6
python -m etl empresas --origem "mysql+pymysql://usuario:senha@servidor:3306/requinte"
python -m etl funcionarios --origem "mysql+pymysql://..." --empresa 01
python -m etl clientes --origem "mysql+pymysql://..." --empresa 01 --avisos avisos-01.txt
python -m etl fornecedores --origem "mysql+pymysql://..." --empresa 01 --avisos fornecedores-01.txt
python -m etl usuarios --origem "mysql+pymysql://..." --empresa 01
python -m etl estoque --origem "mysql+pymysql://..." --empresa 01 --avisos estoque-01.txt
python -m etl produtos --origem "mysql+pymysql://.../requinte" --empresa 01 --outras "mysql+pymysql://.../requintejun" --avisos produtos.txt
```

O destino é o banco do `.env`. Rode uma vez para cada banco de filial, nesta ordem: empresas, funcionários (os cobradores dos setores são funcionários), clientes, fornecedores e usuários (depois dos funcionários). A lista de cidades do IBGE vem da migração 0008 (`alembic upgrade head`). O `--empresa` diz de qual empresa é o banco de origem.

### MariaDB local sem senha

Se os bancos foram baixados para um MariaDB local em que o root entra pela autenticação do Windows (sem senha), o pymysql não consegue entrar. Use o conector da MariaDB, que vem no extra `legado` no Windows:

```bash
python -m etl funcionarios --origem "mariadb+mariadbconnector://root@127.0.0.1:3306/requinte" --empresa 01
```

### Funcionários

- Cargos e funcionários são ligados aos códigos antigos pela tabela `legado_mapa` (tabela de origem + empresa + código), porque `cod_fun` e `cod_car` se repetem entre filiais. Cargo que não está no mapa é procurado pelo nome.
- A maior parte dos funcionários está cadastrada em mais de uma filial, às vezes até duas vezes na mesma. Funcionário que não está no mapa é procurado:
  1. pelo CPF, se os nomes forem compatíveis (abreviações e nomes incompletos passam). Há cadastros que não são de pessoas, como "ESCRITORIO" ou nome de shopping, com o CPF do dono: esses viram cadastro à parte, sem CPF, com aviso;
  2. sem CPF que identifique, pelo nome completo (sem acentos e sem diferenciar maiúsculas), entre os que vieram de outra filial. Mesmo nome na mesma filial são duas pessoas;
  3. se não achar, é criado, com a loja de origem como lotação.
- Quem manda nos dados de uma pessoa que está em várias filiais é a loja de lotação. As outras filiais só preenchem campos vazios e acrescentam telefones. Se a pessoa está inativa na lotação e ativa em outra filial, ela passa para essa filial. Quem está ativo em duas filiais fica na primeira importada: rode a matriz primeiro e ajuste na ficha se precisar.
- Na reimportação, os dados do VB6 atualizam o cadastro, menos a loja de lotação.
- Telefones vêm da `tab_telefones` com `tipo_ter = 'U'`; só entram os que ainda não existem.
- CPFs inválidos (muitos são `000.000.000-01` ou `5555...`) são ignorados. Tudo o que foi ignorado, separado ou ligado com nome diferente sai como aviso no fim, para conferência.

### Clientes

Decisão D15. Lê `tab_grupocli`, `tab_tipopar` (parentescos das referências), `tab_cidades`, `tab_setores`, `tab_orgaos`, `tab_clientes`, `tab_telefones` (`tipo_ter = 'C'`), `tab_referencias` e `tab_clientesanot`.

- Grupos, parentescos e órgãos são juntados pelo nome, e setores pelo nome e pela cidade, sem acentos e sem diferenciar maiúsculas. O mesmo código significa coisas diferentes em cada filial, por isso cada código fica no `legado_mapa` com a empresa de origem.
- O cobrador do setor (`cobrador_set`) é o código de um funcionário da loja (D17): ele é somado aos cobradores que o setor já tem, que valem para todas as lojas. Rode antes o ETL de funcionários; código que não está no mapa de funcionários sai como aviso.
- O cliente não tem cidade nem bairro: são os do setor. A `bairro_cli`, a `cidade_cli`, a `uf_cli` e o `cod_cid` da `tab_clientes` não são importados.
- O setor do funcionário (`cod_set` da `tab_funcionarios`) é ligado aqui, depois dos setores. Manda a loja onde ele está lotado; as outras só preenchem o vazio.
- A cidade do setor é a do IBGE: pelo `cod_mun` da `tab_cidades`, ou pelo nome e UF, ou pela única cidade da UF cujo nome começa assim ("CORUMBA" → Corumbá de Goiás). A que não for achada sai como aviso, e os setores dela ficam sem cidade.
- Cliente é juntado pelo CPF/CNPJ válido.
- Cliente sem CPF/CNPJ válido ou com nome sem sentido ("TESTE", "+", um endereço) não é importado (D21), a não ser que tenha parcela de crediário em aberto na loja (`tab_doc` com `tipo_ter = 'C'` e `tab_itdoc.reman_itd` > 0). Se já estava no banco novo, é excluído, menos quando veio também de outra loja ou tem documentos enviados no sistema novo. Os que ficam por causa da dívida são cadastro próprio da filial (sem documento, não há como juntar com outra loja). Cadastro repetido com nome sem sentido (o "+" do cadastro velho, com o mesmo CPF do novo) nunca manda nos dados, mesmo sendo o alterado por último; o código dele não fica no mapa, então vendas e parcelas desse código acham o cliente pelo CPF.
- Erros de digitação no nome são corrigidos: zero no lugar da letra O e pedaços de endereço no fim do nome ("N.470", "Q 3 L 2").
- Manda nos dados o registro com a data de alteração mais recente (`dataalt_cli`, ou `data_cli`). Os outros só preenchem campos vazios; telefones, referências e anotações (menos as excluídas) são somados. Data e loja do cadastro são as do registro mais antigo.
- As colunas da `tab_clientes` e da `tab_orgaos` variam entre filiais; a leitura usa as que existirem e lê tudo como texto, porque datas inválidas e inteiros zerofill quebram o conector da MariaDB.
- O endereço vem de `logradouro`, `numero` e `complemento`; se estiverem vazios, de `logradouro_cli`, `numero_cli` e `complemento_cli`; a `endereco_cli` (campo antigo) só quando os dois estão vazios.
- `status_cli` 2 vira `bloqueado`; `cobranca_cli` 1, 2 e 3 viram `domicilio`, `trabalho` e `loja`.
- Com dezenas de milhares de clientes, a leitura é feita em lotes de mil, com os índices de CPF e do mapa em memória: a matriz leva cerca de um minuto.
- Os avisos (quase todos CPFs inválidos) podem passar de mil por filial: use `--avisos arquivo.txt`.

### Fornecedores

Decisão D22. Lê `tab_fornecedores` e `tab_telefones` (`tipo_ter = 'F'`, com o `cod_for` no `cod_cli`).

- Fornecedor é juntado pelo CPF/CNPJ. Sem CPF/CNPJ válido ou com nome sem sentido, não entra; se já tinha entrado por esta loja e não veio de outra, sai.
- A tabela não tem data de alteração: manda a loja de menor código que tem o fornecedor. As outras só preenchem o vazio e somam telefones e contatos.
- A cidade é procurada pelo nome e pela UF, com as abreviações por extenso ("STA BARBARA DOESTE" → Santa Bárbara d'Oeste), ou pela única cidade da UF que começa assim ("SAO BERNARDO DO CAMP"). A que não for achada sai como aviso.
- O endereço vem da `endereco_for` (com o número junto, como foi digitado) ou da `logradouro_for`.
- `telefone_for` vira telefone comercial e `fax_for`, fax. Os números perdem o zero da operadora ("(0..19)3807-7511" → 1938077511).
- O `contato_for` é texto livre com nome e telefone ("EBSON 9971-0002"): vira um contato. Sem nome ("FAX 15-3284-5809"), o número vai para os telefones do fornecedor.
- O `email_for` é o e-mail do fornecedor; `codantigo_for` não é importado.

### Usuários

Decisão D23. Lê `tab_usuarios` com o `status_fun` da `tab_funcionarios`. Rode antes o ETL de funcionários.

- Entram só os usuários ativos de funcionários ativos. O login é o apelido em minúsculas; se já for de outra pessoa, ganha um número no fim. Um login criado à mão, sem funcionário e com o mesmo apelido, é ligado ao funcionário (sem mexer na senha).
- A mesma pessoa em várias lojas é um usuário só, com um acesso em cada loja, no perfil do nível que tinha nela (1 Operador, 2 Supervisor, 3 Gerente, 4 Gestor). Os perfis são criados sem permissões.
- A senha do VB6 entra como provisória; manda a da loja de lotação. Senha já trocada no sistema novo não muda. Usuário sem senha no VB6 sai como aviso.
- Na reimportação, o acesso de quem ficou inativo no VB6 é desligado, e o perfil mudado na tela continua.
- As permissões por usuário da `tab_defusu` não são importadas.

### Produtos

Decisão D24. Lê `tab_secoes`, `tab_subsec`, `tab_produtos` e `tab_codbarras` só do banco da matriz, que é quem mantém o cadastro. Rode antes o ETL de fornecedores da matriz. Com `--outras`, lê também as vendas e compras dos bancos das outras lojas, só para saber se o produto está ativo.

- O `cod_pro` vira o código do produto; as vendas e o estoque das lojas acham o produto por ele. Seções e subseções ficam no `legado_mapa`. Nome de seção com lixo no fim ("CAMA)</item") é cortado; subseção de seção que não existe vai para DIVERSOS.
- Custo: `cf_pro` (o da última nota), ou o `cr_pro` se estiver zerado. Preço: `pv_pro`. Margem: `lucro_pro`. Queima: `pq_pro`, se for menor que o preço. O `pa_pro` (atacado) não vem.
- Códigos de barras de `tab_codbarras`, `ean_pro` e `codbarra_pro`, só com 8 a 14 dígitos. O igual ao próprio código não vem (o código já é o código interno); o igual ao código de outro produto também não, por ser ambíguo. Repetido em dois produtos fica no de código maior.
- O `cod_fab` é o fornecedor (código da `tab_fornecedores`). Fornecedor descartado por falta de CNPJ sai como aviso, e o produto fica sem ele.
- Aceita fração: `fracionado_pro = 'S'`, ou já vendido com quantidade quebrada.
- Ativo: vendido (venda não cancelada), comprado, ou cadastrado ou alterado (`dataalt_pro`) no último ano, na matriz ou nas `--outras`.
- Na reimportação, os dados voltam a ser os do VB6; códigos de barras e fornecedores acrescentados no sistema novo ficam.
- Princípio ativo, controle, fabricante, gênero, combustível e balança (restos de farmácia) não são importados. O estoque fica para o ETL do estoque.

### Estoque

Decisão D24. Lê a `tab_produtos` e a `tab_consignacoes` de cada loja. Rode antes o ETL de produtos.

- O produto é achado pelo código. Código que a matriz não tem, ou que na loja é outro produto (nome bem diferente do da matriz), fica de fora, com aviso.
- Quantidade: `ef_pro` (o fiscal, que passa a ser o real). Ele inclui o que está com os representantes, porque no VB6 a consignação mexe só no `er_pro`.
- Reservado: soma do `reman_con` da `tab_consignacoes` (o que falta acertar), a mesma conta que o VB6 usa para refazer o `r_pro`.
- Localização (`endereco_pro`, sem os "UN" e "0" que sobraram de outro campo), CST/CSOSN (`cst_icms`) e CFOP (`cfop_pro`).
- Cada diferença de saldo vira um movimento "Saldo do VB6"; na reimportação entra só a diferença. Produto sem saldo, reservado e localização não ganha linha.
- É o saldo de partida: depois ele vai ser refeito a partir do inventário de 31/12/2025, com as notas desde então.

## Situação

| Parte | Status |
|---|---|
| Conversão de senhas (`senha_legado.py`) | pronta, com testes |
| Agente das filiais | a fazer |
| Carga da área de chegada | a fazer |
| Importação de empresas (`empresas.py`) | pronta, com testes |
| Importação de funcionários e cargos (`funcionarios.py`) | pronta, com testes |
| Importação de clientes, setores, órgãos e grupos (`clientes.py`) | pronta, com testes |
| Importação de fornecedores (`fornecedores.py`) | pronta, com testes |
| Importação de usuários (`usuarios.py`) | pronta, com testes |
| Importação de produtos, seções e subseções (`produtos.py`) | pronta, com testes |
| Importação do estoque de cada loja (`estoque.py`) | pronta, com testes |
| Demais domínios | acompanham as ondas do roteiro |
