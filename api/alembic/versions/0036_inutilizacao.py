"""inutilização de números das notas (D29)

As faixas de números que não vão ser usadas (as lacunas da série), homologadas
pela SEFAZ. A nota rejeitada cujo número foi inutilizado fica "inutilizada"
(a situação passa a caber 12 letras).

Revisão: 0036
Anterior: 0035
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0036'
down_revision: str | None = '0035'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('nota_inutilizacao',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('ambiente', sa.String(length=1), nullable=False),
    sa.Column('modelo', sa.String(length=2), nullable=False),
    sa.Column('serie', sa.Integer(), nullable=False),
    sa.Column('inicial', sa.Integer(), nullable=False),
    sa.Column('final', sa.Integer(), nullable=False),
    sa.Column('justificativa', sa.String(length=255), nullable=False),
    sa.Column('protocolo', sa.String(length=15), nullable=True),
    sa.Column('homologada_em', sa.DateTime(), nullable=True),
    sa.Column('feita_por_id', sa.Integer(), nullable=False),
    sa.Column('xml', sa.Text(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_nota_inutilizacao_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['feita_por_id'], ['usuario.id'], name=op.f('fk_nota_inutilizacao_feita_por_id_usuario')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_nota_inutilizacao'))
    )
    op.create_index(op.f('ix_nota_inutilizacao_empresa_id'), 'nota_inutilizacao', ['empresa_id'], unique=False)
    with op.batch_alter_table('nota_fiscal') as batch:
        batch.alter_column('situacao', existing_type=sa.String(length=10), type_=sa.String(length=12),
                           existing_nullable=False)


def downgrade() -> None:
    op.execute("UPDATE nota_fiscal SET situacao = 'rejeitada' WHERE situacao = 'inutilizada'")
    with op.batch_alter_table('nota_fiscal') as batch:
        batch.alter_column('situacao', existing_type=sa.String(length=12), type_=sa.String(length=10),
                           existing_nullable=False)
    op.drop_index(op.f('ix_nota_inutilizacao_empresa_id'), table_name='nota_inutilizacao')
    op.drop_table('nota_inutilizacao')
