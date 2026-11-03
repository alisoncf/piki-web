"""prejuízo da parcela (D26)

A parcela que não se espera mais receber (o cliente morreu, não foi achado,
a cobrança desistiu) cai no prejuízo: quando, quem e por quê. Ela sai da lista
do contas a receber, mas o cliente continua devendo.

Revisão: 0027
Anterior: 0026
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0027'
down_revision: str | None = '0026'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('conta_receber_parcela') as batch:
        batch.add_column(sa.Column('prejuizo_em', sa.DateTime(), nullable=True))
        batch.add_column(sa.Column('prejuizo_por_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('prejuizo_motivo', sa.String(length=200), nullable=True))
        batch.create_foreign_key(op.f('fk_conta_receber_parcela_prejuizo_por_id_usuario'), 'usuario',
                                 ['prejuizo_por_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('conta_receber_parcela') as batch:
        batch.drop_constraint(op.f('fk_conta_receber_parcela_prejuizo_por_id_usuario'), type_='foreignkey')
        batch.drop_column('prejuizo_motivo')
        batch.drop_column('prejuizo_por_id')
        batch.drop_column('prejuizo_em')
