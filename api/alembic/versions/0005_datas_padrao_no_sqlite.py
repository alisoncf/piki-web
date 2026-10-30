"""datas padrao que funcionam tambem no SQLite

A 0004 foi gerada com server_default text('now()'), que o SQLite não tem.
sa.func.now() vira now() no PostgreSQL (nada muda lá) e CURRENT_TIMESTAMP no SQLite.

Revisão: 0005
Anterior: 0004
Criada em: 2026-10-30
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0005'
down_revision: str | None = '0004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABELAS = ('cargo', 'funcionario', 'legado_mapa')


def _trocar(padrao) -> None:
    for tabela in _TABELAS:
        with op.batch_alter_table(tabela, schema=None) as batch_op:
            for coluna in ('criado_em', 'atualizado_em'):
                batch_op.alter_column(coluna, existing_type=sa.DateTime(), existing_nullable=False, server_default=padrao)


def upgrade() -> None:
    _trocar(sa.func.now())


def downgrade() -> None:
    _trocar(sa.text('now()'))
