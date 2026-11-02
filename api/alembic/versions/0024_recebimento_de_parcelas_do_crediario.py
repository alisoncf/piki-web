"""recebimento de parcelas do crediário (D26)

O caixa recebe parcelas do cliente, de qualquer loja, toda ou parte de cada
uma, com os juros de atraso, em uma ou mais formas. A forma Crediário guarda o
% ao mês dos juros de atraso (5%, como hoje no VB6).

Revisão: 0024
Anterior: 0023
Criada em: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0024'
down_revision: str | None = '0023'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('recebimento_crediario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('sessao_caixa_id', sa.Integer(), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=False),
    sa.Column('data_hora', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('valor_recebido', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('estornado_em', sa.DateTime(), nullable=True),
    sa.Column('estornado_por_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], name=op.f('fk_recebimento_crediario_cliente_id_cliente')),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_recebimento_crediario_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['estornado_por_id'], ['usuario.id'], name=op.f('fk_recebimento_crediario_estornado_por_id_usuario')),
    sa.ForeignKeyConstraint(['sessao_caixa_id'], ['caixa_sessao.id'], name=op.f('fk_recebimento_crediario_sessao_caixa_id_caixa_sessao')),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_recebimento_crediario_usuario_id_usuario')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recebimento_crediario'))
    )
    op.create_index(op.f('ix_recebimento_crediario_cliente_id'), 'recebimento_crediario', ['cliente_id'], unique=False)
    op.create_index(op.f('ix_recebimento_crediario_empresa_id'), 'recebimento_crediario', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_recebimento_crediario_sessao_caixa_id'), 'recebimento_crediario', ['sessao_caixa_id'], unique=False)
    op.create_table('recebimento_crediario_pagamento',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recebimento_id', sa.Integer(), nullable=False),
    sa.Column('forma_pagamento_id', sa.Integer(), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['forma_pagamento_id'], ['forma_pagamento.id'], name=op.f('fk_recebimento_crediario_pagamento_forma_pagamento_id_forma_pagamento')),
    sa.ForeignKeyConstraint(['recebimento_id'], ['recebimento_crediario.id'], name=op.f('fk_recebimento_crediario_pagamento_recebimento_id_recebimento_crediario'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recebimento_crediario_pagamento'))
    )
    op.create_index(op.f('ix_recebimento_crediario_pagamento_recebimento_id'), 'recebimento_crediario_pagamento', ['recebimento_id'], unique=False)
    op.create_table('recebimento_crediario_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recebimento_id', sa.Integer(), nullable=False),
    sa.Column('parcela_id', sa.Integer(), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('juros', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['parcela_id'], ['conta_receber_parcela.id'], name=op.f('fk_recebimento_crediario_item_parcela_id_conta_receber_parcela')),
    sa.ForeignKeyConstraint(['recebimento_id'], ['recebimento_crediario.id'], name=op.f('fk_recebimento_crediario_item_recebimento_id_recebimento_crediario'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recebimento_crediario_item'))
    )
    op.create_index(op.f('ix_recebimento_crediario_item_parcela_id'), 'recebimento_crediario_item', ['parcela_id'], unique=False)
    op.create_index(op.f('ix_recebimento_crediario_item_recebimento_id'), 'recebimento_crediario_item', ['recebimento_id'], unique=False)
    with op.batch_alter_table('forma_pagamento') as batch:
        batch.add_column(sa.Column('juros_atraso', sa.Numeric(precision=5, scale=2), server_default='0', nullable=False))
    op.execute("update forma_pagamento set juros_atraso = 5 where tipo = 'crediario'")


def downgrade() -> None:
    with op.batch_alter_table('forma_pagamento') as batch:
        batch.drop_column('juros_atraso')
    op.drop_index(op.f('ix_recebimento_crediario_item_recebimento_id'), table_name='recebimento_crediario_item')
    op.drop_index(op.f('ix_recebimento_crediario_item_parcela_id'), table_name='recebimento_crediario_item')
    op.drop_table('recebimento_crediario_item')
    op.drop_index(op.f('ix_recebimento_crediario_pagamento_recebimento_id'), table_name='recebimento_crediario_pagamento')
    op.drop_table('recebimento_crediario_pagamento')
    op.drop_index(op.f('ix_recebimento_crediario_sessao_caixa_id'), table_name='recebimento_crediario')
    op.drop_index(op.f('ix_recebimento_crediario_empresa_id'), table_name='recebimento_crediario')
    op.drop_index(op.f('ix_recebimento_crediario_cliente_id'), table_name='recebimento_crediario')
    op.drop_table('recebimento_crediario')
