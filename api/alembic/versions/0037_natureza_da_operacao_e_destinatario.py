"""natureza da operação das notas e destinatário na lista (D29)

A natureza (natOp), o tipo, a finalidade e o CFOP de dentro e de fora do estado de
cada operação que gera nota (venda, remessa, retorno de remessa, devolução),
editáveis para conferir com o contador; as linhas são criadas pela API com os
valores do VB6. Na nota, o nome do destinatário, para a lista.

Revisão: 0037
Anterior: 0036
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0037'
down_revision: str | None = '0036'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('nota_operacao',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uso', sa.String(length=20), nullable=False),
    sa.Column('natureza', sa.String(length=60), nullable=False),
    sa.Column('tipo', sa.String(length=1), nullable=False),
    sa.Column('finalidade', sa.String(length=1), nullable=False),
    sa.Column('cfop_estado', sa.String(length=4), nullable=False),
    sa.Column('cfop_fora', sa.String(length=4), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_nota_operacao')),
    sa.UniqueConstraint('uso', name=op.f('uq_nota_operacao_uso'))
    )
    with op.batch_alter_table('nota_fiscal') as batch:
        batch.add_column(sa.Column('destinatario', sa.String(length=60), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('nota_fiscal') as batch:
        batch.drop_column('destinatario')
    op.drop_table('nota_operacao')
