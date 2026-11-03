"""tipo de cobrança da parcela (D27)

Como o cliente vai pagar, escolhido por ele quando a venda é efetivada:
pagamento na loja, cobrança no cliente, representante recebe, depósito ou
boleto (tab_tipocob do VB6). O ETL traz o cod_tip das parcelas.

Revisão: 0029
Anterior: 0028
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0029'
down_revision: str | None = '0028'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('conta_receber_parcela') as batch:
        batch.add_column(sa.Column('tipo_cobranca', sa.String(length=15), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('conta_receber_parcela') as batch:
        batch.drop_column('tipo_cobranca')
