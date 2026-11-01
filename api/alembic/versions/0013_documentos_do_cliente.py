"""documentos do cliente (crediário)

cliente_documento guarda o tipo, quem enviou e a chave do arquivo, que fica
fora do banco (numa pasta do servidor ou no MinIO, ver app/nucleo/arquivos.py).

Revisão: 0013
Anterior: 0012
Criada em: 2026-11-01
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0013'
down_revision: str | None = '0012'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('cliente_documento',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cliente_id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.String(length=20), nullable=False),
    sa.Column('descricao', sa.String(length=60), nullable=True),
    sa.Column('nome_arquivo', sa.String(length=120), nullable=False),
    sa.Column('tipo_conteudo', sa.String(length=30), nullable=False),
    sa.Column('tamanho', sa.Integer(), nullable=False),
    sa.Column('chave', sa.String(length=200), nullable=False),
    sa.Column('data_hora', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=True),
    sa.Column('empresa_id', sa.Integer(), nullable=True),
    sa.Column('removido_em', sa.DateTime(), nullable=True),
    sa.Column('removido_por_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['cliente_id'], ['cliente.id'], name=op.f('fk_cliente_documento_cliente_id_cliente'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_cliente_documento_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['removido_por_id'], ['usuario.id'], name=op.f('fk_cliente_documento_removido_por_id_usuario')),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], name=op.f('fk_cliente_documento_usuario_id_usuario')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cliente_documento')),
    sa.UniqueConstraint('chave', name=op.f('uq_cliente_documento_chave'))
    )
    op.create_index(op.f('ix_cliente_documento_cliente_id'), 'cliente_documento', ['cliente_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_cliente_documento_cliente_id'), table_name='cliente_documento')
    op.drop_table('cliente_documento')
