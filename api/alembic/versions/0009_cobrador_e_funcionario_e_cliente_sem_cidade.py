"""cobrador é funcionário e cliente sem cidade

- setor_cobrador passa a ligar o setor a funcionários (muitos para muitos, sem
  loja); a tabela cobrador, criada na 0008, deixa de existir;
- cliente perde cidade, uf e codigo_municipio: a cidade do cliente é a do setor.

Os cobradores dos setores se perdem aqui: rode de novo o ETL de clientes de
cada loja (python -m etl clientes), que os liga aos funcionários.

Revisão: 0009
Anterior: 0008
Criada em: 2026-10-31
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0009'
down_revision: str | None = '0008'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _datas() -> list[sa.Column]:
    return [
        sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    ]


def _setor_cobrador(coluna: str, tabela: str) -> None:
    op.create_table('setor_cobrador',
    sa.Column('setor_id', sa.Integer(), nullable=False),
    sa.Column(coluna, sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint([coluna], [f'{tabela}.id'], name=op.f(f'fk_setor_cobrador_{coluna}_{tabela}'),
                            ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['setor_id'], ['setor.id'], name=op.f('fk_setor_cobrador_setor_id_setor'),
                            ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('setor_id', coluna, name=op.f('pk_setor_cobrador'))
    )


def upgrade() -> None:
    op.drop_table('setor_cobrador')
    op.drop_table('cobrador')
    _setor_cobrador('funcionario_id', 'funcionario')

    with op.batch_alter_table('cliente') as batch_op:
        batch_op.drop_column('cidade')
        batch_op.drop_column('uf')
        batch_op.drop_column('codigo_municipio')


def downgrade() -> None:
    with op.batch_alter_table('cliente') as batch_op:
        batch_op.add_column(sa.Column('cidade', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('uf', sa.String(length=2), nullable=True))
        batch_op.add_column(sa.Column('codigo_municipio', sa.String(length=7), nullable=True))

    op.drop_table('setor_cobrador')
    op.create_table('cobrador',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=40), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    *_datas(),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cobrador')),
    sa.UniqueConstraint('nome', name=op.f('uq_cobrador_nome'))
    )
    _setor_cobrador('cobrador_id', 'cobrador')
