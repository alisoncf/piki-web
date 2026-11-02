"""venda fechada, consumidor, entrega e queima (D26)

O cadastro curto de quem compra sem ser cliente cadastrado, o nome de quem
comprou na venda (o caixa acha por ele), a venda fechada pelo vendedor, a
entrega com taxa e endereço, e o item vendido em queima (sem desconto).

Revisão: 0022
Anterior: 0021
Criada em: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0022'
down_revision: str | None = '0021'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('consumidor',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=60), nullable=False),
    sa.Column('cpf', sa.String(length=11), nullable=True),
    sa.Column('dia_nascimento', sa.SmallInteger(), nullable=True),
    sa.Column('mes_nascimento', sa.SmallInteger(), nullable=True),
    sa.Column('telefone', sa.String(length=15), nullable=True),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_consumidor')),
    sa.UniqueConstraint('cpf', name=op.f('uq_consumidor_cpf'))
    )
    op.create_table('venda_entrega',
    sa.Column('venda_id', sa.Integer(), nullable=False),
    sa.Column('taxa', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('cep', sa.String(length=8), nullable=True),
    sa.Column('logradouro', sa.String(length=100), nullable=True),
    sa.Column('numero', sa.String(length=20), nullable=True),
    sa.Column('complemento', sa.String(length=60), nullable=True),
    sa.Column('bairro', sa.String(length=60), nullable=True),
    sa.Column('cidade_id', sa.Integer(), nullable=True),
    sa.Column('ponto_referencia', sa.String(length=60), nullable=True),
    sa.Column('telefone', sa.String(length=15), nullable=True),
    sa.ForeignKeyConstraint(['cidade_id'], ['cidade.id'], name=op.f('fk_venda_entrega_cidade_id_cidade')),
    sa.ForeignKeyConstraint(['venda_id'], ['venda.id'], name=op.f('fk_venda_entrega_venda_id_venda'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('venda_id', name=op.f('pk_venda_entrega'))
    )
    with op.batch_alter_table('venda') as batch:
        batch.add_column(sa.Column('consumidor_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('comprador', sa.String(length=60), nullable=True))
        batch.add_column(sa.Column('fechada_em', sa.DateTime(), nullable=True))
        batch.create_index(op.f('ix_venda_comprador'), ['comprador'], unique=False)
        batch.create_index(op.f('ix_venda_consumidor_id'), ['consumidor_id'], unique=False)
        batch.create_foreign_key(op.f('fk_venda_consumidor_id_consumidor'), 'consumidor', ['consumidor_id'], ['id'])
    with op.batch_alter_table('venda_item') as batch:
        batch.add_column(sa.Column('em_queima', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    # as vendas que já existem: o comprador é o cliente cadastrado
    op.execute("update venda set comprador = (select nome from cliente where cliente.id = venda.cliente_id) "
               "where cliente_id is not null")


def downgrade() -> None:
    with op.batch_alter_table('venda_item') as batch:
        batch.drop_column('em_queima')
    with op.batch_alter_table('venda') as batch:
        batch.drop_constraint(op.f('fk_venda_consumidor_id_consumidor'), type_='foreignkey')
        batch.drop_index(op.f('ix_venda_consumidor_id'))
        batch.drop_index(op.f('ix_venda_comprador'))
        batch.drop_column('fechada_em')
        batch.drop_column('comprador')
        batch.drop_column('consumidor_id')
    op.drop_table('venda_entrega')
    op.drop_table('consumidor')
