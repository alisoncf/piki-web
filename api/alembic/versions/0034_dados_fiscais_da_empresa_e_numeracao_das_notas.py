"""dados fiscais da empresa e numeração das notas (D29)

Na empresa: o ambiente da SEFAZ, o certificado A1 (o arquivo fica numa pasta do
servidor; a senha, cifrada) e o CSC da NFC-e (o token, cifrado). No caixa, a
série das notas (101 é o caixa 01, como no VB6); as que já existem recebem a
série pelo código do caixa no VB6, quando o ETL rodar de novo. E o último número
de cada modelo e série da loja.

Revisão: 0034
Anterior: 0033
Criada em: 2026-11-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0034'
down_revision: str | None = '0033'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('nota_numeracao',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('modelo', sa.String(length=2), nullable=False),
    sa.Column('serie', sa.Integer(), nullable=False),
    sa.Column('ultimo', sa.Integer(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_nota_numeracao_empresa_id_empresa')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_nota_numeracao')),
    sa.UniqueConstraint('empresa_id', 'modelo', 'serie', name=op.f('uq_nota_numeracao_empresa_id'))
    )
    op.create_index(op.f('ix_nota_numeracao_empresa_id'), 'nota_numeracao', ['empresa_id'], unique=False)
    with op.batch_alter_table('caixa') as batch:
        batch.add_column(sa.Column('serie_nfe', sa.Integer(), nullable=True))
    with op.batch_alter_table('empresa') as batch:
        batch.add_column(sa.Column('nfe_ambiente', sa.String(length=1), server_default='2', nullable=False))
        batch.add_column(sa.Column('certificado_arquivo', sa.String(length=100), nullable=True))
        batch.add_column(sa.Column('certificado_senha', sa.Text(), nullable=True))
        batch.add_column(sa.Column('certificado_titular', sa.String(length=200), nullable=True))
        batch.add_column(sa.Column('certificado_validade', sa.DateTime(), nullable=True))
        batch.add_column(sa.Column('csc_id', sa.String(length=10), nullable=True))
        batch.add_column(sa.Column('csc_token', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('empresa') as batch:
        for coluna in ('csc_token', 'csc_id', 'certificado_validade', 'certificado_titular', 'certificado_senha',
                       'certificado_arquivo', 'nfe_ambiente'):
            batch.drop_column(coluna)
    with op.batch_alter_table('caixa') as batch:
        batch.drop_column('serie_nfe')
    op.drop_index(op.f('ix_nota_numeracao_empresa_id'), table_name='nota_numeracao')
    op.drop_table('nota_numeracao')
