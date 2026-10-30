"""funcionarios, cargos e mapa do legado

Revisão: 0004
Anterior: 0003
Criada em: 2026-10-30
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0004'
down_revision: str | None = '0003'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('cargo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=40), nullable=False),
    sa.Column('vende', sa.Boolean(), nullable=False),
    sa.Column('cobra', sa.Boolean(), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cargo')),
    sa.UniqueConstraint('nome', name=op.f('uq_cargo_nome'))
    )
    op.create_table('funcionario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=80), nullable=False),
    sa.Column('apelido', sa.String(length=30), nullable=True),
    sa.Column('cpf', sa.String(length=11), nullable=True),
    sa.Column('rg', sa.String(length=20), nullable=True),
    sa.Column('data_nascimento', sa.Date(), nullable=True),
    sa.Column('sexo', sa.String(length=1), nullable=True),
    sa.Column('naturalidade', sa.String(length=40), nullable=True),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('cargo_id', sa.Integer(), nullable=True),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('pode_tirar_vale', sa.Boolean(), nullable=False),
    sa.Column('limite_vale', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('cep', sa.String(length=8), nullable=True),
    sa.Column('logradouro', sa.String(length=60), nullable=True),
    sa.Column('bairro', sa.String(length=40), nullable=True),
    sa.Column('cidade', sa.String(length=40), nullable=True),
    sa.Column('uf', sa.String(length=2), nullable=True),
    sa.Column('conjuge', sa.String(length=60), nullable=True),
    sa.Column('pai', sa.String(length=60), nullable=True),
    sa.Column('mae', sa.String(length=60), nullable=True),
    sa.Column('endereco_pais', sa.String(length=100), nullable=True),
    sa.Column('observacao', sa.Text(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['cargo_id'], ['cargo.id'], name=op.f('fk_funcionario_cargo_id_cargo')),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_funcionario_empresa_id_empresa')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_funcionario')),
    sa.UniqueConstraint('cpf', name=op.f('uq_funcionario_cpf'))
    )
    op.create_table('legado_mapa',
    sa.Column('tabela', sa.String(length=40), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=20), nullable=False),
    sa.Column('novo_id', sa.Integer(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_legado_mapa_empresa_id_empresa')),
    sa.PrimaryKeyConstraint('tabela', 'empresa_id', 'codigo', name=op.f('pk_legado_mapa'))
    )
    op.create_table('funcionario_telefone',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('funcionario_id', sa.Integer(), nullable=False),
    sa.Column('numero', sa.String(length=15), nullable=False),
    sa.Column('tipo', sa.String(length=1), nullable=False),
    sa.ForeignKeyConstraint(['funcionario_id'], ['funcionario.id'], name=op.f('fk_funcionario_telefone_funcionario_id_funcionario'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_funcionario_telefone'))
    )
    op.create_index(op.f('ix_funcionario_telefone_funcionario_id'), 'funcionario_telefone', ['funcionario_id'], unique=False)
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.add_column(sa.Column('funcionario_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint(batch_op.f('uq_usuario_funcionario_id'), ['funcionario_id'])
        batch_op.create_foreign_key(batch_op.f('fk_usuario_funcionario_id_funcionario'), 'funcionario',
                                    ['funcionario_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_usuario_funcionario_id_funcionario'), type_='foreignkey')
        batch_op.drop_constraint(batch_op.f('uq_usuario_funcionario_id'), type_='unique')
        batch_op.drop_column('funcionario_id')
    op.drop_index(op.f('ix_funcionario_telefone_funcionario_id'), table_name='funcionario_telefone')
    op.drop_table('funcionario_telefone')
    op.drop_table('legado_mapa')
    op.drop_table('funcionario')
    op.drop_table('cargo')
