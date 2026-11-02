"""fornecedores (D22)

fornecedor é cadastro global, sempre com CPF ou CNPJ válido; os telefones da
empresa ficam em fornecedor_telefone e as pessoas (representante,
financeiro...) em fornecedor_contato.

Revisão: 0014
Anterior: 0013
Criada em: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0014'
down_revision: str | None = '0013'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('fornecedor',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=100), nullable=False),
    sa.Column('nome_fantasia', sa.String(length=60), nullable=True),
    sa.Column('cpf_cnpj', sa.String(length=14), nullable=False),
    sa.Column('inscricao_estadual', sa.String(length=20), nullable=True),
    sa.Column('cep', sa.String(length=8), nullable=True),
    sa.Column('logradouro', sa.String(length=60), nullable=True),
    sa.Column('numero', sa.String(length=10), nullable=True),
    sa.Column('complemento', sa.String(length=60), nullable=True),
    sa.Column('bairro', sa.String(length=60), nullable=True),
    sa.Column('cidade_id', sa.Integer(), nullable=True),
    sa.Column('email', sa.String(length=200), nullable=True),
    sa.Column('site', sa.String(length=200), nullable=True),
    sa.Column('observacao', sa.Text(), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['cidade_id'], ['cidade.id'], name=op.f('fk_fornecedor_cidade_id_cidade')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fornecedor')),
    sa.UniqueConstraint('cpf_cnpj', name=op.f('uq_fornecedor_cpf_cnpj'))
    )
    op.create_index(op.f('ix_fornecedor_cidade_id'), 'fornecedor', ['cidade_id'], unique=False)
    op.create_table('fornecedor_contato',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fornecedor_id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=60), nullable=False),
    sa.Column('funcao', sa.String(length=40), nullable=True),
    sa.Column('telefone', sa.String(length=15), nullable=True),
    sa.Column('email', sa.String(length=200), nullable=True),
    sa.ForeignKeyConstraint(['fornecedor_id'], ['fornecedor.id'], name=op.f('fk_fornecedor_contato_fornecedor_id_fornecedor'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fornecedor_contato'))
    )
    op.create_index(op.f('ix_fornecedor_contato_fornecedor_id'), 'fornecedor_contato', ['fornecedor_id'], unique=False)
    op.create_table('fornecedor_telefone',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('fornecedor_id', sa.Integer(), nullable=False),
    sa.Column('numero', sa.String(length=15), nullable=False),
    sa.Column('tipo', sa.String(length=1), nullable=False),
    sa.ForeignKeyConstraint(['fornecedor_id'], ['fornecedor.id'], name=op.f('fk_fornecedor_telefone_fornecedor_id_fornecedor'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fornecedor_telefone'))
    )
    op.create_index(op.f('ix_fornecedor_telefone_fornecedor_id'), 'fornecedor_telefone', ['fornecedor_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_fornecedor_telefone_fornecedor_id'), table_name='fornecedor_telefone')
    op.drop_table('fornecedor_telefone')
    op.drop_index(op.f('ix_fornecedor_contato_fornecedor_id'), table_name='fornecedor_contato')
    op.drop_table('fornecedor_contato')
    op.drop_index(op.f('ix_fornecedor_cidade_id'), table_name='fornecedor')
    op.drop_table('fornecedor')
