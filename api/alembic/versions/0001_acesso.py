"""acesso: empresas, usuarios, perfis e permissoes

Revisão: 0001
Anterior: nenhuma
Criada em: 2026-10-30
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('empresa',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=2), nullable=False),
    sa.Column('nome', sa.String(length=60), nullable=False),
    sa.Column('razao_social', sa.String(length=100), nullable=True),
    sa.Column('cnpj', sa.String(length=14), nullable=True),
    sa.Column('ativa', sa.Boolean(), server_default=sa.true(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_empresa')),
    sa.UniqueConstraint('cnpj', name=op.f('uq_empresa_cnpj')),
    sa.UniqueConstraint('codigo', name=op.f('uq_empresa_codigo'))
    )
    op.create_table('perfil',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=50), nullable=False),
    sa.Column('descricao', sa.String(length=150), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_perfil')),
    sa.UniqueConstraint('nome', name=op.f('uq_perfil_nome'))
    )
    op.create_table('permissao',
    sa.Column('codigo', sa.String(length=50), nullable=False),
    sa.Column('descricao', sa.String(length=150), nullable=False),
    sa.PrimaryKeyConstraint('codigo', name=op.f('pk_permissao'))
    )
    op.create_table('perfil_permissao',
    sa.Column('perfil_id', sa.Integer(), nullable=False),
    sa.Column('permissao_codigo', sa.String(length=50), nullable=False),
    sa.ForeignKeyConstraint(['perfil_id'], ['perfil.id'], name=op.f('fk_perfil_permissao_perfil_id_perfil'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['permissao_codigo'], ['permissao.codigo'], name=op.f('fk_perfil_permissao_permissao_codigo_permissao'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('perfil_id', 'permissao_codigo', name=op.f('pk_perfil_permissao'))
    )
    op.create_table('usuario',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(length=30), nullable=False),
    sa.Column('nome', sa.String(length=80), nullable=False),
    sa.Column('hash_senha', sa.String(length=255), nullable=True),
    sa.Column('senha_sem_caixa', sa.Boolean(), nullable=False),
    sa.Column('administrador', sa.Boolean(), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('ultimo_login', sa.DateTime(), nullable=True),
    sa.Column('ultima_empresa_id', sa.Integer(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['ultima_empresa_id'], ['empresa.id'], name=op.f('fk_usuario_ultima_empresa_id_empresa'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usuario')),
    sa.UniqueConstraint('login', name=op.f('uq_usuario_login'))
    )
    op.create_table('usuario_empresa',
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('perfil_id', sa.Integer(), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_usuario_empresa_empresa_id_empresa'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['perfil_id'], ['perfil.id'], name=op.f('fk_usuario_empresa_perfil_id_perfil')),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_usuario_empresa_usuario_id_usuario'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('usuario_id', 'empresa_id', name=op.f('pk_usuario_empresa'))
    )


def downgrade() -> None:
    op.drop_table('usuario_empresa')
    op.drop_table('usuario')
    op.drop_table('perfil_permissao')
    op.drop_table('permissao')
    op.drop_table('perfil')
    op.drop_table('empresa')
