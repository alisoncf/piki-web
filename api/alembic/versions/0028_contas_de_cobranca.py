"""contas de cobrança (D27)

Onde o carnê está para ser cobrado (tab_contacob do VB6): a Geral (na loja,
sem estar com ninguém), um cobrador, o advogado, um balanço... Uma lista só
para todas as lojas. Toda parcela está numa conta; as que já existem vão para
a Geral, e o ETL traz a conta do VB6.

Revisão: 0028
Anterior: 0027
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0028'
down_revision: str | None = '0027'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('conta_cobranca',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=40), nullable=False),
    sa.Column('padrao', sa.Boolean(), server_default=sa.false(), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conta_cobranca')),
    sa.UniqueConstraint('nome', name=op.f('uq_conta_cobranca_nome'))
    )
    op.execute("insert into conta_cobranca (nome, padrao, ativo) values ('Geral', true, true)")
    with op.batch_alter_table('conta_receber_parcela') as batch:
        batch.add_column(sa.Column('conta_cobranca_id', sa.Integer(), nullable=True))
    op.execute("update conta_receber_parcela set conta_cobranca_id = (select id from conta_cobranca where padrao)")
    with op.batch_alter_table('conta_receber_parcela') as batch:
        batch.alter_column('conta_cobranca_id', existing_type=sa.Integer(), nullable=False)
        batch.create_index(op.f('ix_conta_receber_parcela_conta_cobranca_id'), ['conta_cobranca_id'], unique=False)
        batch.create_foreign_key(op.f('fk_conta_receber_parcela_conta_cobranca_id_conta_cobranca'), 'conta_cobranca',
                                 ['conta_cobranca_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('conta_receber_parcela') as batch:
        batch.drop_constraint(op.f('fk_conta_receber_parcela_conta_cobranca_id_conta_cobranca'), type_='foreignkey')
        batch.drop_index(op.f('ix_conta_receber_parcela_conta_cobranca_id'))
        batch.drop_column('conta_cobranca_id')
    op.drop_table('conta_cobranca')
