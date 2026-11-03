"""histórico da parcela (D27)

As mudanças da parcela e do documento dela: prorrogações (de quando para
quando, com a anotação do contato), conta e tipo de cobrança, prejuízo e
cabeçalho do documento, com quem e quando (como a frmEdiLan do VB6).

Revisão: 0030
Anterior: 0029
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0030'
down_revision: str | None = '0029'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('conta_receber_parcela_historico',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('parcela_id', sa.Integer(), nullable=False),
    sa.Column('mudanca', sa.String(length=15), nullable=False),
    sa.Column('de', sa.String(length=100), nullable=True),
    sa.Column('para', sa.String(length=100), nullable=True),
    sa.Column('anotacao', sa.String(length=500), nullable=True),
    sa.Column('data_hora', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parcela_id'], ['conta_receber_parcela.id'], name=op.f('fk_conta_receber_parcela_historico_parcela_id_conta_receber_parcela'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_conta_receber_parcela_historico_usuario_id_usuario')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conta_receber_parcela_historico'))
    )
    op.create_index(op.f('ix_conta_receber_parcela_historico_parcela_id'), 'conta_receber_parcela_historico', ['parcela_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_conta_receber_parcela_historico_parcela_id'), table_name='conta_receber_parcela_historico')
    op.drop_table('conta_receber_parcela_historico')
