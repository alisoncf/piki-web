"""devoluções do consignado (D30)

O representante devolve produtos à loja: a devolução (aberta no balcão,
confirmada com a senha dele; a retificadora corrige uma transferência errada) e
os itens, cada um ligado ao item de transferência de onde a peça volta.

Revisão: 0040
Anterior: 0039
Criada em: 2026-11-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0040'
down_revision: str | None = '0039'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('consignacao_devolucao',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('numero', sa.Integer(), nullable=False),
    sa.Column('representante_id', sa.Integer(), nullable=False),
    sa.Column('situacao', sa.String(length=10), nullable=False),
    sa.Column('retificadora', sa.Boolean(), nullable=False),
    sa.Column('observacao', sa.String(length=200), nullable=True),
    sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('atendida_por_id', sa.Integer(), nullable=False),
    sa.Column('autorizada_por_id', sa.Integer(), nullable=True),
    sa.Column('confirmada_em', sa.DateTime(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['atendida_por_id'], ['usuario.id'], name=op.f('fk_consignacao_devolucao_atendida_por_id_usuario')),
    sa.ForeignKeyConstraint(['autorizada_por_id'], ['usuario.id'], name=op.f('fk_consignacao_devolucao_autorizada_por_id_usuario')),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_consignacao_devolucao_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['representante_id'], ['representante.id'], name=op.f('fk_consignacao_devolucao_representante_id_representante')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_devolucao')),
    sa.UniqueConstraint('empresa_id', 'numero', name=op.f('uq_consignacao_devolucao_empresa_id'))
    )
    op.create_index(op.f('ix_consignacao_devolucao_empresa_id'), 'consignacao_devolucao', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_consignacao_devolucao_representante_id'), 'consignacao_devolucao', ['representante_id'], unique=False)
    op.create_index(op.f('ix_consignacao_devolucao_situacao'), 'consignacao_devolucao', ['situacao'], unique=False)
    op.create_table('consignacao_devolucao_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('devolucao_id', sa.Integer(), nullable=False),
    sa.Column('ordem', sa.Integer(), nullable=False),
    sa.Column('item_transferencia_id', sa.Integer(), nullable=False),
    sa.Column('quantidade', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.ForeignKeyConstraint(['devolucao_id'], ['consignacao_devolucao.id'], name=op.f('fk_consignacao_devolucao_item_devolucao_id_consignacao_devolucao'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['item_transferencia_id'], ['consignacao_transferencia_item.id'], name=op.f('fk_consignacao_devolucao_item_item_transferencia_id_consignacao_transferencia_item')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_devolucao_item'))
    )
    op.create_index(op.f('ix_consignacao_devolucao_item_devolucao_id'), 'consignacao_devolucao_item', ['devolucao_id'], unique=False)
    op.create_index(op.f('ix_consignacao_devolucao_item_item_transferencia_id'), 'consignacao_devolucao_item', ['item_transferencia_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_consignacao_devolucao_item_item_transferencia_id'), table_name='consignacao_devolucao_item')
    op.drop_index(op.f('ix_consignacao_devolucao_item_devolucao_id'), table_name='consignacao_devolucao_item')
    op.drop_table('consignacao_devolucao_item')
    op.drop_index(op.f('ix_consignacao_devolucao_situacao'), table_name='consignacao_devolucao')
    op.drop_index(op.f('ix_consignacao_devolucao_representante_id'), table_name='consignacao_devolucao')
    op.drop_index(op.f('ix_consignacao_devolucao_empresa_id'), table_name='consignacao_devolucao')
    op.drop_table('consignacao_devolucao')
