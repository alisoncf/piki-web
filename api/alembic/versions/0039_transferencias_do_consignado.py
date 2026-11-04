"""transferências do consignado (D30)

O representante leva produtos para o estoque dele: a transferência (aberta no
balcão, confirmada com a senha dele) e os itens, cada um com o preço de venda do
dia e o que ainda resta com ele. No VB6 não havia cabeçalho (tab_consignacoes).

Revisão: 0039
Anterior: 0038
Criada em: 2026-11-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0039'
down_revision: str | None = '0038'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('consignacao_transferencia',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('numero', sa.Integer(), nullable=False),
    sa.Column('representante_id', sa.Integer(), nullable=False),
    sa.Column('situacao', sa.String(length=10), nullable=False),
    sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('atendida_por_id', sa.Integer(), nullable=False),
    sa.Column('confirmada_em', sa.DateTime(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['atendida_por_id'], ['usuario.id'], name=op.f('fk_consignacao_transferencia_atendida_por_id_usuario')),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_consignacao_transferencia_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['representante_id'], ['representante.id'], name=op.f('fk_consignacao_transferencia_representante_id_representante')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_transferencia')),
    sa.UniqueConstraint('empresa_id', 'numero', name=op.f('uq_consignacao_transferencia_empresa_id'))
    )
    op.create_index(op.f('ix_consignacao_transferencia_empresa_id'), 'consignacao_transferencia', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_consignacao_transferencia_representante_id'), 'consignacao_transferencia', ['representante_id'], unique=False)
    op.create_index(op.f('ix_consignacao_transferencia_situacao'), 'consignacao_transferencia', ['situacao'], unique=False)
    op.create_table('consignacao_transferencia_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('transferencia_id', sa.Integer(), nullable=False),
    sa.Column('ordem', sa.Integer(), nullable=False),
    sa.Column('produto_id', sa.Integer(), nullable=False),
    sa.Column('descricao', sa.String(length=120), nullable=False),
    sa.Column('quantidade', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('preco', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('restante', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.ForeignKeyConstraint(['produto_id'], ['produto.id'], name=op.f('fk_consignacao_transferencia_item_produto_id_produto')),
    sa.ForeignKeyConstraint(['transferencia_id'], ['consignacao_transferencia.id'], name=op.f('fk_consignacao_transferencia_item_transferencia_id_consignacao_transferencia'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_transferencia_item'))
    )
    op.create_index(op.f('ix_consignacao_transferencia_item_produto_id'), 'consignacao_transferencia_item', ['produto_id'], unique=False)
    op.create_index(op.f('ix_consignacao_transferencia_item_transferencia_id'), 'consignacao_transferencia_item', ['transferencia_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_consignacao_transferencia_item_transferencia_id'), table_name='consignacao_transferencia_item')
    op.drop_index(op.f('ix_consignacao_transferencia_item_produto_id'), table_name='consignacao_transferencia_item')
    op.drop_table('consignacao_transferencia_item')
    op.drop_index(op.f('ix_consignacao_transferencia_situacao'), table_name='consignacao_transferencia')
    op.drop_index(op.f('ix_consignacao_transferencia_representante_id'), table_name='consignacao_transferencia')
    op.drop_index(op.f('ix_consignacao_transferencia_empresa_id'), table_name='consignacao_transferencia')
    op.drop_table('consignacao_transferencia')
