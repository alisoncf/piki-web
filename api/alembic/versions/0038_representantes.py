"""representantes do consignado (D30)

O representante é um cliente especializado: aqui ficam o código (o do VB6), a
situação, o limite, a senha (hash), os bloqueios, os lembretes, o avalista e as
comissões próprias por tipo de cobrança (sem elas, vale a padrão do tipo).

Revisão: 0038
Anterior: 0037
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0038'
down_revision: str | None = '0037'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('representante',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.Integer(), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('bloqueado', sa.Boolean(), nullable=False),
    sa.Column('motivo_bloqueio', sa.Text(), nullable=True),
    sa.Column('limite', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('senha_hash', sa.String(length=200), nullable=True),
    sa.Column('bloqueia_impressao', sa.Boolean(), nullable=False),
    sa.Column('bloqueia_devolucao', sa.Boolean(), nullable=False),
    sa.Column('lembrete', sa.Text(), nullable=True),
    sa.Column('lembrete_acerto', sa.Text(), nullable=True),
    sa.Column('observacao', sa.Text(), nullable=True),
    sa.Column('ultima_conferencia', sa.Date(), nullable=True),
    sa.Column('data_cadastro', sa.Date(), nullable=False),
    sa.Column('avalista_nome', sa.String(length=100), nullable=True),
    sa.Column('avalista_cpf', sa.String(length=11), nullable=True),
    sa.Column('avalista_rg', sa.String(length=20), nullable=True),
    sa.Column('avalista_endereco', sa.String(length=200), nullable=True),
    sa.Column('avalista_telefones', sa.String(length=200), nullable=True),
    sa.Column('avalista_anotacoes', sa.Text(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], name=op.f('fk_representante_cliente_id_cliente')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_representante')),
    sa.UniqueConstraint('cliente_id', name=op.f('uq_representante_cliente_id')),
    sa.UniqueConstraint('codigo', name=op.f('uq_representante_codigo'))
    )
    op.create_table('representante_comissao',
    sa.Column('representante_id', sa.Integer(), nullable=False),
    sa.Column('tipo_cobranca', sa.String(length=15), nullable=False),
    sa.Column('percentual', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['representante_id'], ['representante.id'], name=op.f('fk_representante_comissao_representante_id_representante'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('representante_id', 'tipo_cobranca', name=op.f('pk_representante_comissao'))
    )


def downgrade() -> None:
    op.drop_table('representante_comissao')
    op.drop_table('representante')
