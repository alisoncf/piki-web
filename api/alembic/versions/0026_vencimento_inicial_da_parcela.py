"""vencimento inicial da parcela (D26)

O vencimento com que a parcela nasceu (vencini_itd do VB6); o vencimento
muda quando a parcela é prorrogada. A tela de contas a receber filtra pelos
dois. As parcelas que já existem recebem o vencimento atual; o ETL traz o do
VB6 na próxima importação.

Revisão: 0026
Anterior: 0025
Criada em: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0026'
down_revision: str | None = '0025'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('conta_receber_parcela') as batch:
        batch.add_column(sa.Column('vencimento_inicial', sa.Date(), nullable=True))
    op.execute("update conta_receber_parcela set vencimento_inicial = vencimento")


def downgrade() -> None:
    with op.batch_alter_table('conta_receber_parcela') as batch:
        batch.drop_column('vencimento_inicial')
