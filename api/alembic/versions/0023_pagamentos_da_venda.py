"""pagamentos da venda (D26)

No caixa, o cliente paga em uma ou mais formas (um pouco no PIX, um pouco no
cartão); no crediário, esses pagamentos são a entrada. A venda guarda a data
base do crediário e o modelo da nota (65 NFC-e ou 55 NF-e). A entrada da 0021
vira pagamento.

Revisão: 0023
Anterior: 0022
Criada em: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0023'
down_revision: str | None = '0022'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('venda_pagamento',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('venda_id', sa.Integer(), nullable=False),
    sa.Column('ordem', sa.Integer(), nullable=False),
    sa.Column('forma_pagamento_id', sa.Integer(), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('parcelas', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['forma_pagamento_id'], ['forma_pagamento.id'], name=op.f('fk_venda_pagamento_forma_pagamento_id_forma_pagamento')),
    sa.ForeignKeyConstraint(['venda_id'], ['venda.id'], name=op.f('fk_venda_pagamento_venda_id_venda'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_venda_pagamento'))
    )
    op.create_index(op.f('ix_venda_pagamento_venda_id'), 'venda_pagamento', ['venda_id'], unique=False)
    with op.batch_alter_table('venda') as batch:
        batch.add_column(sa.Column('data_base', sa.Date(), nullable=True))
        batch.add_column(sa.Column('modelo_nota', sa.String(length=2), server_default='65', nullable=False))

    # as vendas já recebidas: no crediário, a entrada vira pagamento e a data base é o dia do recebimento;
    # nas outras formas, o total foi pago na forma da venda
    op.execute("""
        insert into venda_pagamento (venda_id, ordem, forma_pagamento_id, valor, parcelas)
        select id, 1, forma_entrada_id, entrada, 1 from venda
        where situacao = 'recebida' and forma_entrada_id is not null and entrada > 0
    """)
    op.execute("""
        insert into venda_pagamento (venda_id, ordem, forma_pagamento_id, valor, parcelas)
        select v.id, 1, v.forma_pagamento_id, v.total, v.parcelas from venda v
        join forma_pagamento f on f.id = v.forma_pagamento_id
        where v.situacao = 'recebida' and f.tipo <> 'crediario' and v.total > 0
    """)
    op.execute("""
        update venda set data_base = cast(recebida_em as date)
        where situacao = 'recebida' and entrada is not null
    """)

    with op.batch_alter_table('venda') as batch:
        batch.drop_constraint('fk_venda_forma_entrada_id_forma_pagamento', type_='foreignkey')
        batch.drop_column('forma_entrada_id')
        batch.drop_column('entrada')


def downgrade() -> None:
    with op.batch_alter_table('venda') as batch:
        batch.add_column(sa.Column('entrada', sa.Numeric(precision=14, scale=2), nullable=True))
        batch.add_column(sa.Column('forma_entrada_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_venda_forma_entrada_id_forma_pagamento', 'forma_pagamento', ['forma_entrada_id'], ['id'])
        batch.drop_column('modelo_nota')
        batch.drop_column('data_base')
    op.drop_index(op.f('ix_venda_pagamento_venda_id'), table_name='venda_pagamento')
    op.drop_table('venda_pagamento')
