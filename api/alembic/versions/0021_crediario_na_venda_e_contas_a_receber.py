"""crediário na venda e contas a receber (D26)

O carnê (conta a receber e parcelas) e, na venda, a entrada do crediário e quem
autorizou passar do limite do cliente.

Revisão: 0021
Anterior: 0020
Criada em: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0021'
down_revision: str | None = '0020'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('conta_receber',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=False),
    sa.Column('venda_id', sa.Integer(), nullable=True),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('historico', sa.String(length=80), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], name=op.f('fk_conta_receber_cliente_id_cliente')),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_conta_receber_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_conta_receber_usuario_id_usuario')),
    sa.ForeignKeyConstraint(['venda_id'], ['venda.id'], name=op.f('fk_conta_receber_venda_id_venda')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conta_receber')),
    sa.UniqueConstraint('venda_id', name=op.f('uq_conta_receber_venda_id'))
    )
    op.create_index(op.f('ix_conta_receber_cliente_id'), 'conta_receber', ['cliente_id'], unique=False)
    op.create_index(op.f('ix_conta_receber_empresa_id'), 'conta_receber', ['empresa_id'], unique=False)
    op.create_table('conta_receber_parcela',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conta_id', sa.Integer(), nullable=False),
    sa.Column('numero', sa.Integer(), nullable=False),
    sa.Column('vencimento', sa.Date(), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('aberto', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['conta_id'], ['conta_receber.id'], name=op.f('fk_conta_receber_parcela_conta_id_conta_receber'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conta_receber_parcela')),
    sa.UniqueConstraint('conta_id', 'numero', name=op.f('uq_conta_receber_parcela_conta_id'))
    )
    op.create_index(op.f('ix_conta_receber_parcela_conta_id'), 'conta_receber_parcela', ['conta_id'], unique=False)
    op.create_index(op.f('ix_conta_receber_parcela_vencimento'), 'conta_receber_parcela', ['vencimento'], unique=False)
    with op.batch_alter_table('venda') as batch:
        batch.add_column(sa.Column('entrada', sa.Numeric(precision=14, scale=2), nullable=True))
        batch.add_column(sa.Column('forma_entrada_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('limite_autorizado_por_id', sa.Integer(), nullable=True))
        batch.create_foreign_key(op.f('fk_venda_forma_entrada_id_forma_pagamento'), 'forma_pagamento', ['forma_entrada_id'], ['id'])
        batch.create_foreign_key(op.f('fk_venda_limite_autorizado_por_id_usuario'), 'usuario', ['limite_autorizado_por_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('venda') as batch:
        batch.drop_constraint(op.f('fk_venda_limite_autorizado_por_id_usuario'), type_='foreignkey')
        batch.drop_constraint(op.f('fk_venda_forma_entrada_id_forma_pagamento'), type_='foreignkey')
        batch.drop_column('limite_autorizado_por_id')
        batch.drop_column('forma_entrada_id')
        batch.drop_column('entrada')
    op.drop_index(op.f('ix_conta_receber_parcela_vencimento'), table_name='conta_receber_parcela')
    op.drop_index(op.f('ix_conta_receber_parcela_conta_id'), table_name='conta_receber_parcela')
    op.drop_table('conta_receber_parcela')
    op.drop_index(op.f('ix_conta_receber_empresa_id'), table_name='conta_receber')
    op.drop_index(op.f('ix_conta_receber_cliente_id'), table_name='conta_receber')
    op.drop_table('conta_receber')
