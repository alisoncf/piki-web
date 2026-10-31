"""setor do funcionário e cliente sem bairro

- funcionario perde bairro, cidade e uf e ganha setor_id: bairro e cidade
  são os do setor, como no cliente (D17);
- cliente perde bairro, campo de antes dos setores que não é mais usado.

O setor dos funcionários é preenchido pelo ETL de clientes (python -m etl
clientes), a partir do cod_set da tab_funcionarios.

Revisão: 0010
Anterior: 0009
Criada em: 2026-10-31
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0010'
down_revision: str | None = '0009'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('funcionario') as batch_op:
        batch_op.drop_column('bairro')
        batch_op.drop_column('cidade')
        batch_op.drop_column('uf')
        batch_op.add_column(sa.Column('setor_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(op.f('fk_funcionario_setor_id_setor'), 'setor', ['setor_id'], ['id'])
        batch_op.create_index(op.f('ix_funcionario_setor_id'), ['setor_id'], unique=False)

    with op.batch_alter_table('cliente') as batch_op:
        batch_op.drop_column('bairro')


def downgrade() -> None:
    with op.batch_alter_table('cliente') as batch_op:
        batch_op.add_column(sa.Column('bairro', sa.String(length=40), nullable=True))

    with op.batch_alter_table('funcionario') as batch_op:
        batch_op.drop_index(op.f('ix_funcionario_setor_id'))
        batch_op.drop_constraint(op.f('fk_funcionario_setor_id_setor'), type_='foreignkey')
        batch_op.drop_column('setor_id')
        batch_op.add_column(sa.Column('bairro', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('cidade', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('uf', sa.String(length=2), nullable=True))
