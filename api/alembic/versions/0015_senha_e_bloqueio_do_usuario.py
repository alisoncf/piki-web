"""senha provisória, bloqueio do login e e-mail do usuário

trocar_senha obriga a trocar a senha no próximo login; tentativas_erradas e
bloqueado_ate bloqueiam o login depois de cinco senhas erradas seguidas.

Revisão: 0015
Anterior: 0014
Criada em: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0015'
down_revision: str | None = '0014'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('usuario') as t:
        t.add_column(sa.Column('email', sa.String(length=200), nullable=True))
        t.add_column(sa.Column('trocar_senha', sa.Boolean(), server_default=sa.false(), nullable=False))
        t.add_column(sa.Column('tentativas_erradas', sa.Integer(), server_default='0', nullable=False))
        t.add_column(sa.Column('bloqueado_ate', sa.DateTime(), nullable=True))
        t.create_unique_constraint(op.f('uq_usuario_email'), ['email'])


def downgrade() -> None:
    with op.batch_alter_table('usuario') as t:
        t.drop_constraint(op.f('uq_usuario_email'), type_='unique')
        t.drop_column('bloqueado_ate')
        t.drop_column('tentativas_erradas')
        t.drop_column('trocar_senha')
        t.drop_column('email')
