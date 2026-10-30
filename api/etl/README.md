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

### Funcionários

- Cargos e funcionários são ligados aos códigos antigos pela tabela `legado_mapa` (tabela de origem + empresa + código), porque `cod_fun` e `cod_car` se repetem entre filiais.
- Funcionário que não está no mapa é procurado pelo CPF: a mesma pessoa em duas filiais vira um cadastro só, e os dados da primeira importação ficam. Sem CPF válido, é criado um cadastro novo.
- Na reimportação, os dados do VB6 atualizam o cadastro, menos a loja de lotação.
- Telefones vêm da `tab_telefones` com `tipo_ter = 'U'`; só entram os que ainda não existem.
- CPFs inválidos são ignorados e aparecem como aviso no fim.

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
