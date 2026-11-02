"""contas a receber importadas do VB6 (D26)

A conta guarda de onde veio (venda, acerto de consignação ou avulsa) e o
número do documento no VB6, que se repete entre as lojas e só identifica junto
com a loja. Quem lançou pode faltar nas contas antigas.

Revisão: 0025
Anterior: 0024
Criada em: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0025'
down_revision: str | None = '0024'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('conta_receber') as batch:
        batch.add_column(sa.Column('origem', sa.String(length=10), server_default='venda', nullable=False))
        batch.add_column(sa.Column('documento_legado', sa.String(length=20), nullable=True))
        batch.alter_column('usuario_id', existing_type=sa.INTEGER(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('conta_receber') as batch:
        batch.alter_column('usuario_id', existing_type=sa.INTEGER(), nullable=False)
        batch.drop_column('documento_legado')
        batch.drop_column('origem')
