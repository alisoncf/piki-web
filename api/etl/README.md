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
```

O destino é o banco do `.env`. Rode uma vez para cada banco de filial, nesta ordem: empresas, funcionários (os cobradores dos setores são funcionários) e clientes. A lista de cidades do IBGE vem da migração 0008 (`alembic upgrade head`). O `--empresa` diz de qual empresa é o banco de origem.

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
- Cliente é juntado pelo CPF/CNPJ válido. Sem documento válido, vira cadastro próprio da filial (não junta pelo nome: em 30/10/2026, a La Viva tinha 23 mil clientes assim).
- Manda nos dados o registro com a data de alteração mais recente (`dataalt_cli`, ou `data_cli`). Os outros só preenchem campos vazios; telefones, referências e anotações (menos as excluídas) são somados. Data e loja do cadastro são as do registro mais antigo.
- As colunas da `tab_clientes` e da `tab_orgaos` variam entre filiais; a leitura usa as que existirem e lê tudo como texto, porque datas inválidas e inteiros zerofill quebram o conector da MariaDB.
- O endereço vem de `logradouro`, `numero` e `complemento`; se estiverem vazios, de `logradouro_cli`, `numero_cli` e `complemento_cli`; a `endereco_cli` (campo antigo) só quando os dois estão vazios.
- `status_cli` 2 vira `bloqueado`; `cobranca_cli` 1, 2 e 3 viram `domicilio`, `trabalho` e `loja`.
- Com dezenas de milhares de clientes, a leitura é feita em lotes de mil, com os índices de CPF e do mapa em memória: a matriz leva cerca de um minuto.
- Os avisos (quase todos CPFs inválidos) podem passar de mil por filial: use `--avisos arquivo.txt`.

## Situação

| Parte | Status |
|---|---|
| Conversão de senhas (`senha_legado.py`) | pronta, com testes |
| Agente das filiais | a fazer |
| Carga da área de chegada | a fazer |
| Importação de empresas (`empresas.py`) | pronta, com testes |
| Importação de funcionários e cargos (`funcionarios.py`) | pronta, com testes |
| Importação de clientes, setores, órgãos e grupos (`clientes.py`) | pronta, com testes |
| Importação de usuários | a fazer |
| Demais domínios | acompanham as ondas do roteiro |
