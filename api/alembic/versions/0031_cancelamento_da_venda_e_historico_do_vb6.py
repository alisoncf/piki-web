"""cancelamento da venda e histórico do VB6 (D26, D27)

O carnê da venda cancelada guarda quando foi cancelado. O histórico da parcela
ganha a chave do que veio do VB6 (tab_itdocpre: loja e seq_pre), para a
reimportação não repetir.

Revisão: 0031
Anterior: 0030
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0031'
down_revision: str | None = '0030'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('conta_receber') as batch:
        batch.add_column(sa.Column('cancelada_em', sa.DateTime(), nullable=True))
    with op.batch_alter_table('conta_receber_parcela_historico') as batch:
        batch.add_column(sa.Column('legado', sa.String(length=20), nullable=True))
        batch.create_unique_constraint(op.f('uq_conta_receber_parcela_historico_legado'), ['legado'])


def downgrade() -> None:
    with op.batch_alter_table('conta_receber_parcela_historico') as batch:
        batch.drop_constraint(op.f('uq_conta_receber_parcela_historico_legado'), type_='unique')
        batch.drop_column('legado')
    with op.batch_alter_table('conta_receber') as batch:
        batch.drop_column('cancelada_em')
