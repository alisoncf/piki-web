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
```

O destino é o banco do `.env`. Rode uma vez para cada banco de filial, começando pelas empresas. O `--empresa` diz de qual empresa é o banco de origem.

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

## Situação

| Parte | Status |
|---|---|
| Conversão de senhas (`senha_legado.py`) | pronta, com testes |
| Agente das filiais | a fazer |
| Carga da área de chegada | a fazer |
| Importação de empresas (`empresas.py`) | pronta, com testes |
| Importação de funcionários e cargos (`funcionarios.py`) | pronta, com testes |
| Importação de usuários | a fazer |
| Demais domínios | acompanham as ondas do roteiro |
