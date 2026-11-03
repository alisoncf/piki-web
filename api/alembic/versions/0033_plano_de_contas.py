"""plano de contas (D28)

As contas de receita e de despesa, cadastráveis, uma lista só para todas as
lojas. Começa com as do VB6 (sem importar: as lojas cadastram as suas depois).
A despesa e a outra entrada do caixa passam a levar a conta.

Revisão: 0033
Anterior: 0032
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0033'
down_revision: str | None = '0032'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INICIAIS = {
    "receita": ["Vendas de produtos", "Venda de produtos consignados", "Aluguel recebido", "Receitas diversas"],
    "despesa": ["Água, luz e energia", "Aluguel", "Combustíveis", "Compra de mercadorias", "Pagamento de funcionários",
                "Pró-labore", "Gastos de chefia", "Juros e multas", "Investimentos", "Despesas diversas"],
}


def upgrade() -> None:
    tabela = op.create_table('plano_conta',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.String(length=10), nullable=False),
    sa.Column('nome', sa.String(length=60), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_plano_conta')),
    sa.UniqueConstraint('tipo', 'nome', name=op.f('uq_plano_conta_tipo'))
    )
    op.bulk_insert(tabela, [{"tipo": tipo, "nome": nome, "ativo": True}
                            for tipo, nomes in INICIAIS.items() for nome in nomes])
    with op.batch_alter_table('caixa_lancamento') as batch:
        batch.add_column(sa.Column('plano_conta_id', sa.Integer(), nullable=True))
        batch.create_foreign_key(op.f('fk_caixa_lancamento_plano_conta_id_plano_conta'), 'plano_conta',
                                 ['plano_conta_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('caixa_lancamento') as batch:
        batch.drop_constraint(op.f('fk_caixa_lancamento_plano_conta_id_plano_conta'), type_='foreignkey')
        batch.drop_column('plano_conta_id')
    op.drop_table('plano_conta')
