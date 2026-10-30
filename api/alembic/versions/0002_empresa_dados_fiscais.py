"""empresa: dados fiscais e endereco

Revisão: 0002
Anterior: 0001
Criada em: 2026-10-30
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0002'
down_revision: str | None = '0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('empresa', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nome_fantasia', sa.String(length=60), nullable=True))
        batch_op.add_column(sa.Column('inscricao_estadual', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('inscricao_municipal', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('crt', sa.String(length=1), nullable=True))
        batch_op.add_column(sa.Column('sped_perfil', sa.String(length=1), nullable=True))
        batch_op.add_column(sa.Column('sped_atividade', sa.String(length=1), nullable=True))
        batch_op.add_column(sa.Column('uf', sa.String(length=2), nullable=True))
        batch_op.add_column(sa.Column('codigo_municipio', sa.String(length=7), nullable=True))
        batch_op.add_column(sa.Column('cep', sa.String(length=8), nullable=True))
        batch_op.add_column(sa.Column('logradouro', sa.String(length=60), nullable=True))
        batch_op.add_column(sa.Column('numero', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('complemento', sa.String(length=60), nullable=True))
        batch_op.add_column(sa.Column('bairro', sa.String(length=60), nullable=True))
        batch_op.add_column(sa.Column('telefone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(length=200), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('empresa', schema=None) as batch_op:
        batch_op.drop_column('email')
        batch_op.drop_column('telefone')
        batch_op.drop_column('bairro')
        batch_op.drop_column('complemento')
        batch_op.drop_column('numero')
        batch_op.drop_column('logradouro')
        batch_op.drop_column('cep')
        batch_op.drop_column('codigo_municipio')
        batch_op.drop_column('uf')
        batch_op.drop_column('sped_atividade')
        batch_op.drop_column('sped_perfil')
        batch_op.drop_column('crt')
        batch_op.drop_column('inscricao_municipal')
        batch_op.drop_column('inscricao_estadual')
        batch_op.drop_column('nome_fantasia')

