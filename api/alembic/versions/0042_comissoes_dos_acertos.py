"""comissões dos acertos: relatório, pagamento e histórico do VB6 (D30)

A comissão de cada parcela passa a ter a empresa, o vencimento e o quanto já
foi pago, e pode vir do VB6 sem o acerto e sem a parcela. Os pagamentos ao
representante saem do caixa e baixam as comissões.

Revisão: 0042
Anterior: 0041
Criada em: 2026-11-08
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0042'
down_revision: str | None = '0041'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('consignacao_comissao_parcela') as batch_op:
        batch_op.add_column(sa.Column('empresa_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('vencimento', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('pago', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('legado', sa.String(length=7), nullable=True))
        batch_op.add_column(sa.Column('acerto_legado', sa.String(length=7), nullable=True))
        batch_op.add_column(sa.Column('data_acerto_legado', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('cliente_legado', sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column('parcela_legado', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('valor_parcela_legado', sa.Numeric(precision=14, scale=2), nullable=True))
    op.execute("""
        UPDATE consignacao_comissao_parcela SET
            empresa_id = (SELECT a.empresa_id FROM consignacao_acerto a WHERE a.id = consignacao_comissao_parcela.acerto_id),
            vencimento = (SELECT p.vencimento FROM conta_receber_parcela p WHERE p.id = consignacao_comissao_parcela.parcela_id)
    """)
    with op.batch_alter_table('consignacao_comissao_parcela') as batch_op:
        batch_op.alter_column('empresa_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('vencimento', existing_type=sa.Date(), nullable=False)
        batch_op.alter_column('pago', existing_type=sa.Numeric(precision=14, scale=2), server_default=None)
        batch_op.alter_column('acerto_id', existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column('parcela_id', existing_type=sa.Integer(), nullable=True)
        batch_op.create_index(batch_op.f('ix_consignacao_comissao_parcela_empresa_id'), ['empresa_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_consignacao_comissao_parcela_vencimento'), ['vencimento'], unique=False)
        batch_op.create_unique_constraint(batch_op.f('uq_consignacao_comissao_parcela_empresa_id'), ['empresa_id', 'legado'])
        batch_op.create_foreign_key(batch_op.f('fk_consignacao_comissao_parcela_empresa_id_empresa'), 'empresa', ['empresa_id'], ['id'])

    op.create_table('consignacao_comissao_pagamento',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('representante_id', sa.Integer(), nullable=False),
    sa.Column('data_hora', sa.DateTime(), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('forma_pagamento_id', sa.Integer(), nullable=True),
    sa.Column('lancamento_id', sa.Integer(), nullable=True),
    sa.Column('usuario_id', sa.Integer(), nullable=True),
    sa.Column('estornado_em', sa.DateTime(), nullable=True),
    sa.Column('estornado_por_id', sa.Integer(), nullable=True),
    sa.Column('legado', sa.String(length=7), nullable=True),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_consignacao_comissao_pagamento_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['estornado_por_id'], ['usuario.id'], name=op.f('fk_consignacao_comissao_pagamento_estornado_por_id_usuario')),
    sa.ForeignKeyConstraint(['forma_pagamento_id'], ['forma_pagamento.id'], name=op.f('fk_consignacao_comissao_pagamento_forma_pagamento_id_forma_pagamento')),
    sa.ForeignKeyConstraint(['lancamento_id'], ['caixa_lancamento.id'], name=op.f('fk_consignacao_comissao_pagamento_lancamento_id_caixa_lancamento')),
    sa.ForeignKeyConstraint(['representante_id'], ['representante.id'], name=op.f('fk_consignacao_comissao_pagamento_representante_id_representante')),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_consignacao_comissao_pagamento_usuario_id_usuario')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_comissao_pagamento')),
    sa.UniqueConstraint('empresa_id', 'legado', name=op.f('uq_consignacao_comissao_pagamento_empresa_id'))
    )
    op.create_index(op.f('ix_consignacao_comissao_pagamento_empresa_id'), 'consignacao_comissao_pagamento', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_consignacao_comissao_pagamento_representante_id'), 'consignacao_comissao_pagamento', ['representante_id'], unique=False)
    op.create_table('consignacao_comissao_baixa',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('pagamento_id', sa.Integer(), nullable=False),
    sa.Column('comissao_id', sa.Integer(), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['comissao_id'], ['consignacao_comissao_parcela.id'], name=op.f('fk_consignacao_comissao_baixa_comissao_id_consignacao_comissao_parcela')),
    sa.ForeignKeyConstraint(['pagamento_id'], ['consignacao_comissao_pagamento.id'], name=op.f('fk_consignacao_comissao_baixa_pagamento_id_consignacao_comissao_pagamento'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consignacao_comissao_baixa'))
    )
    op.create_index(op.f('ix_consignacao_comissao_baixa_comissao_id'), 'consignacao_comissao_baixa', ['comissao_id'], unique=False)
    op.create_index(op.f('ix_consignacao_comissao_baixa_pagamento_id'), 'consignacao_comissao_baixa', ['pagamento_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_consignacao_comissao_baixa_pagamento_id'), table_name='consignacao_comissao_baixa')
    op.drop_index(op.f('ix_consignacao_comissao_baixa_comissao_id'), table_name='consignacao_comissao_baixa')
    op.drop_table('consignacao_comissao_baixa')
    op.drop_index(op.f('ix_consignacao_comissao_pagamento_representante_id'), table_name='consignacao_comissao_pagamento')
    op.drop_index(op.f('ix_consignacao_comissao_pagamento_empresa_id'), table_name='consignacao_comissao_pagamento')
    op.drop_table('consignacao_comissao_pagamento')
    # as linhas importadas do VB6 não têm acerto nem parcela: não cabem na tabela antiga
    op.execute("DELETE FROM consignacao_comissao_parcela WHERE acerto_id IS NULL OR parcela_id IS NULL")
    with op.batch_alter_table('consignacao_comissao_parcela') as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_consignacao_comissao_parcela_empresa_id_empresa'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('uq_consignacao_comissao_parcela_empresa_id'), type_='unique')
        batch_op.drop_index(batch_op.f('ix_consignacao_comissao_parcela_vencimento'))
        batch_op.drop_index(batch_op.f('ix_consignacao_comissao_parcela_empresa_id'))
        batch_op.alter_column('parcela_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('acerto_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('valor_parcela_legado')
        batch_op.drop_column('parcela_legado')
        batch_op.drop_column('cliente_legado')
        batch_op.drop_column('data_acerto_legado')
        batch_op.drop_column('acerto_legado')
        batch_op.drop_column('legado')
        batch_op.drop_column('pago')
        batch_op.drop_column('vencimento')
        batch_op.drop_column('empresa_id')
