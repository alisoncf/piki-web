"""acertos do consignado (D30)

O acerto do que o representante vendeu: para o cliente dele (carnê no nome do
cliente, comissão dividida pelas parcelas) ou para ele mesmo (a comissão vira
desconto), a prazo ou à vista, e o de queima. Os itens saem de cada item de
transferência; o carnê do acerto fica ligado a ele na conta a receber.

Revisão: 0041
Anterior: 0040
Criada em: 2026-11-05
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0041'
down_revision: str | None = '0040'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('consignacao_acerto',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('numero', sa.Integer(), nullable=False),
    sa.Column('representante_id', sa.Integer(), nullable=False),
    sa.Column('situacao', sa.String(length=10), nullable=False),
    sa.Column('para', sa.String(length=13), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=True),
    sa.Column('queima', sa.Boolean(), nullable=False),
    sa.Column('pagamento', sa.String(length=5), nullable=False),
    sa.Column('tipo_comissao', sa.String(length=15), nullable=False),
    sa.Column('percentual', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('total_inicial', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('diferenca', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('comissao', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('parcelas', sa.Integer(), nullable=False),
    sa.Column('primeiro_vencimento', sa.Date(), nullable=True),
    sa.Column('atendida_por_id', sa.Integer(), nullable=False),
    sa.Column('autorizada_por_id', sa.Integer(), nullable=True),
    sa.Column('sessao_caixa_id', sa.Integer(), nullable=True),
    sa.Column('confirmada_em', sa.DateTime(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['atendida_por_id'], ['usuario.id'], name=op.f('fk_consignacao_acerto_atendida_por_id_usuario')),
    sa.ForeignKeyConstraint(['autorizada_por_id'], ['usuario.id'], name=op.f('fk_consignacao_acerto_autorizada_por_id_usuario')),
    sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], name=op.f('fk_consignacao_acerto_cliente_id_cliente')),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_consignacao_acerto_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['representante_id'], ['representante.id'], name=op.f('fk_consignacao_acerto_representante_id_representante')),
    sa.ForeignKeyConstraint(['sessao_caixa_id'], ['caixa_sessao.id'], name=op.f('fk_consignacao_acerto_sessao_caixa_id_caixa_sessao')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_acerto')),
    sa.UniqueConstraint('empresa_id', 'numero', name=op.f('uq_consignacao_acerto_empresa_id'))
    )
    op.create_index(op.f('ix_consignacao_acerto_cliente_id'), 'consignacao_acerto', ['cliente_id'], unique=False)
    op.create_index(op.f('ix_consignacao_acerto_empresa_id'), 'consignacao_acerto', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_consignacao_acerto_representante_id'), 'consignacao_acerto', ['representante_id'], unique=False)
    op.create_index(op.f('ix_consignacao_acerto_sessao_caixa_id'), 'consignacao_acerto', ['sessao_caixa_id'], unique=False)
    op.create_index(op.f('ix_consignacao_acerto_situacao'), 'consignacao_acerto', ['situacao'], unique=False)
    op.create_table('consignacao_acerto_pagamento',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('acerto_id', sa.Integer(), nullable=False),
    sa.Column('ordem', sa.Integer(), nullable=False),
    sa.Column('forma_pagamento_id', sa.Integer(), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('parcelas', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['acerto_id'], ['consignacao_acerto.id'], name=op.f('fk_consignacao_acerto_pagamento_acerto_id_consignacao_acerto'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['forma_pagamento_id'], ['forma_pagamento.id'], name=op.f('fk_consignacao_acerto_pagamento_forma_pagamento_id_forma_pagamento')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_acerto_pagamento'))
    )
    op.create_index(op.f('ix_consignacao_acerto_pagamento_acerto_id'), 'consignacao_acerto_pagamento', ['acerto_id'], unique=False)
    op.create_table('consignacao_acerto_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('acerto_id', sa.Integer(), nullable=False),
    sa.Column('ordem', sa.Integer(), nullable=False),
    sa.Column('item_transferencia_id', sa.Integer(), nullable=False),
    sa.Column('quantidade', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('preco', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['acerto_id'], ['consignacao_acerto.id'], name=op.f('fk_consignacao_acerto_item_acerto_id_consignacao_acerto'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['item_transferencia_id'], ['consignacao_transferencia_item.id'], name=op.f('fk_consignacao_acerto_item_item_transferencia_id_consignacao_transferencia_item')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_acerto_item'))
    )
    op.create_index(op.f('ix_consignacao_acerto_item_acerto_id'), 'consignacao_acerto_item', ['acerto_id'], unique=False)
    op.create_index(op.f('ix_consignacao_acerto_item_item_transferencia_id'), 'consignacao_acerto_item', ['item_transferencia_id'], unique=False)
    op.create_table('consignacao_comissao_parcela',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('acerto_id', sa.Integer(), nullable=False),
    sa.Column('representante_id', sa.Integer(), nullable=False),
    sa.Column('parcela_id', sa.Integer(), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['acerto_id'], ['consignacao_acerto.id'], name=op.f('fk_consignacao_comissao_parcela_acerto_id_consignacao_acerto')),
    sa.ForeignKeyConstraint(['parcela_id'], ['conta_receber_parcela.id'], name=op.f('fk_consignacao_comissao_parcela_parcela_id_conta_receber_parcela')),
    sa.ForeignKeyConstraint(['representante_id'], ['representante.id'], name=op.f('fk_consignacao_comissao_parcela_representante_id_representante')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_comissao_parcela')),
    sa.UniqueConstraint('parcela_id', name=op.f('uq_consignacao_comissao_parcela_parcela_id'))
    )
    op.create_index(op.f('ix_consignacao_comissao_parcela_acerto_id'), 'consignacao_comissao_parcela', ['acerto_id'], unique=False)
    op.create_index(op.f('ix_consignacao_comissao_parcela_representante_id'), 'consignacao_comissao_parcela', ['representante_id'], unique=False)
    with op.batch_alter_table('conta_receber') as batch_op:
        batch_op.add_column(sa.Column('acerto_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint(op.f('uq_conta_receber_acerto_id'), ['acerto_id'])
        batch_op.create_foreign_key(op.f('fk_conta_receber_acerto_id_consignacao_acerto'), 'consignacao_acerto',
                                    ['acerto_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('conta_receber') as batch_op:
        batch_op.drop_constraint(op.f('fk_conta_receber_acerto_id_consignacao_acerto'), type_='foreignkey')
        batch_op.drop_constraint(op.f('uq_conta_receber_acerto_id'), type_='unique')
        batch_op.drop_column('acerto_id')
    op.drop_index(op.f('ix_consignacao_comissao_parcela_representante_id'), table_name='consignacao_comissao_parcela')
    op.drop_index(op.f('ix_consignacao_comissao_parcela_acerto_id'), table_name='consignacao_comissao_parcela')
    op.drop_table('consignacao_comissao_parcela')
    op.drop_index(op.f('ix_consignacao_acerto_item_item_transferencia_id'), table_name='consignacao_acerto_item')
    op.drop_index(op.f('ix_consignacao_acerto_item_acerto_id'), table_name='consignacao_acerto_item')
    op.drop_table('consignacao_acerto_item')
    op.drop_index(op.f('ix_consignacao_acerto_pagamento_acerto_id'), table_name='consignacao_acerto_pagamento')
    op.drop_table('consignacao_acerto_pagamento')
    op.drop_index(op.f('ix_consignacao_acerto_situacao'), table_name='consignacao_acerto')
    op.drop_index(op.f('ix_consignacao_acerto_sessao_caixa_id'), table_name='consignacao_acerto')
    op.drop_index(op.f('ix_consignacao_acerto_representante_id'), table_name='consignacao_acerto')
    op.drop_index(op.f('ix_consignacao_acerto_empresa_id'), table_name='consignacao_acerto')
    op.drop_index(op.f('ix_consignacao_acerto_cliente_id'), table_name='consignacao_acerto')
    op.drop_table('consignacao_acerto')
