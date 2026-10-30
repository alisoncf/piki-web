# Migrações do banco

Scripts SQL numerados, aplicados em ordem, uma vez em cada banco. Só criam ou alteram tabelas do sistema novo (prefixo `web_`), salvo quando a decisão correspondente em `docs/decisoes.md` disser o contrário.

| Script | O que faz |
|---|---|
| `001_web_credencial.sql` | Tabela de senhas com hash do sistema novo (D7) |

Quando o número de scripts crescer, vale trocar por uma ferramenta de migração (Alembic).
