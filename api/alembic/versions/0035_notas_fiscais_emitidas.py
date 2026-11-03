"""notas fiscais emitidas e numeração por ambiente (D29)

A nota emitida pela loja (NFC-e por enquanto), com o XML, a situação na SEFAZ e o
cancelamento. A numeração passa a ser por ambiente: os testes em homologação não
gastam os números de produção; as que já existem são de produção.

Revisão: 0035
Anterior: 0034
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0035'
down_revision: str | None = '0034'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('nota_fiscal',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('ambiente', sa.String(length=1), nullable=False),
    sa.Column('modelo', sa.String(length=2), nullable=False),
    sa.Column('serie', sa.Integer(), nullable=False),
    sa.Column('numero', sa.Integer(), nullable=False),
    sa.Column('codigo_numerico', sa.String(length=8), nullable=False),
    sa.Column('chave', sa.String(length=44), nullable=False),
    sa.Column('situacao', sa.String(length=10), nullable=False),
    sa.Column('venda_id', sa.Integer(), nullable=True),
    sa.Column('emitida_em', sa.DateTime(), nullable=False),
    sa.Column('emitida_por_id', sa.Integer(), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('codigo_retorno', sa.String(length=3), nullable=True),
    sa.Column('motivo_retorno', sa.String(length=255), nullable=True),
    sa.Column('protocolo', sa.String(length=15), nullable=True),
    sa.Column('autorizada_em', sa.DateTime(), nullable=True),
    sa.Column('xml', sa.Text(), nullable=True),
    sa.Column('cancelada_em', sa.DateTime(), nullable=True),
    sa.Column('cancelada_por_id', sa.Integer(), nullable=True),
    sa.Column('justificativa_cancelamento', sa.String(length=255), nullable=True),
    sa.Column('protocolo_cancelamento', sa.String(length=15), nullable=True),
    sa.Column('xml_cancelamento', sa.Text(), nullable=True),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['cancelada_por_id'], ['usuario.id'], name=op.f('fk_nota_fiscal_cancelada_por_id_usuario')),
    sa.ForeignKeyConstraint(['emitida_por_id'], ['usuario.id'], name=op.f('fk_nota_fiscal_emitida_por_id_usuario')),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_nota_fiscal_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['venda_id'], ['venda.id'], name=op.f('fk_nota_fiscal_venda_id_venda')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_nota_fiscal')),
    sa.UniqueConstraint('empresa_id', 'ambiente', 'modelo', 'serie', 'numero', name=op.f('uq_nota_fiscal_empresa_id'))
    )
    op.create_index(op.f('ix_nota_fiscal_chave'), 'nota_fiscal', ['chave'], unique=False)
    op.create_index(op.f('ix_nota_fiscal_empresa_id'), 'nota_fiscal', ['empresa_id'], unique=False)
    op.create_index(op.f('ix_nota_fiscal_situacao'), 'nota_fiscal', ['situacao'], unique=False)
    op.create_index(op.f('ix_nota_fiscal_venda_id'), 'nota_fiscal', ['venda_id'], unique=False)
    with op.batch_alter_table('nota_numeracao') as batch:
        batch.add_column(sa.Column('ambiente', sa.String(length=1), server_default='1', nullable=False))
        batch.drop_constraint(op.f('uq_nota_numeracao_empresa_id'), type_='unique')
        batch.create_unique_constraint(op.f('uq_nota_numeracao_empresa_id'), ['empresa_id', 'ambiente', 'modelo', 'serie'])


def downgrade() -> None:
    op.execute("DELETE FROM nota_numeracao WHERE ambiente <> '1'")
    with op.batch_alter_table('nota_numeracao') as batch:
        batch.drop_constraint(op.f('uq_nota_numeracao_empresa_id'), type_='unique')
        batch.create_unique_constraint(op.f('uq_nota_numeracao_empresa_id'), ['empresa_id', 'modelo', 'serie'])
        batch.drop_column('ambiente')
    op.drop_index(op.f('ix_nota_fiscal_venda_id'), table_name='nota_fiscal')
    op.drop_index(op.f('ix_nota_fiscal_situacao'), table_name='nota_fiscal')
    op.drop_index(op.f('ix_nota_fiscal_empresa_id'), table_name='nota_fiscal')
    op.drop_index(op.f('ix_nota_fiscal_chave'), table_name='nota_fiscal')
    op.drop_table('nota_fiscal')
