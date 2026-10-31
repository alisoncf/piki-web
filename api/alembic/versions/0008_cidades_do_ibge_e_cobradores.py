"""cidades do IBGE e cobradores para todas as lojas

- tabela cidade com os municípios do IBGE (alembic/referencia/municipios_ibge.csv);
- setor deixa de ter cidade e UF digitadas e passa a apontar para a cidade;
- tabela cobrador (tab_contacob do VB6), e setor_cobrador vira a ligação de
  muitos para muitos entre setores e cobradores, sem loja.

Os cobradores e as cidades dos setores já importados se perdem aqui: rode de
novo o ETL de clientes de cada loja (python -m etl clientes), que preenche os dois.

Revisão: 0008
Anterior: 0007
Criada em: 2026-10-31
"""
import csv
import unicodedata
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from alembic import op


revision: str = '0008'
down_revision: str | None = '0007'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_MUNICIPIOS = Path(__file__).resolve().parents[1] / 'referencia' / 'municipios_ibge.csv'


def _nome_de_busca(nome: str) -> str:
    # o mesmo de app.dominios.cidades.modelos.nome_de_busca, copiado para a migração não mudar junto com o app
    sem_acento = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode()
    return ' '.join(sem_acento.lower().split())


def _datas() -> list[sa.Column]:
    return [
        sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    cidade = op.create_table('cidade',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('codigo_ibge', sa.String(length=7), nullable=False),
    sa.Column('nome', sa.String(length=60), nullable=False),
    sa.Column('uf', sa.String(length=2), nullable=False),
    sa.Column('nome_busca', sa.String(length=60), nullable=False),
    *_datas(),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cidade')),
    sa.UniqueConstraint('codigo_ibge', name=op.f('uq_cidade_codigo_ibge'))
    )
    op.create_index(op.f('ix_cidade_nome_busca'), 'cidade', ['nome_busca'], unique=False)
    with _MUNICIPIOS.open(encoding='utf-8', newline='') as arquivo:
        op.bulk_insert(cidade, [{**linha, 'nome_busca': _nome_de_busca(linha['nome'])}
                                for linha in csv.DictReader(arquivo)])

    op.create_table('cobrador',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=40), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    *_datas(),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_cobrador')),
    sa.UniqueConstraint('nome', name=op.f('uq_cobrador_nome'))
    )

    op.drop_table('setor_cobrador')
    op.create_table('setor_cobrador',
    sa.Column('setor_id', sa.Integer(), nullable=False),
    sa.Column('cobrador_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['cobrador_id'], ['cobrador.id'], name=op.f('fk_setor_cobrador_cobrador_id_cobrador'),
                            ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['setor_id'], ['setor.id'], name=op.f('fk_setor_cobrador_setor_id_setor'),
                            ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('setor_id', 'cobrador_id', name=op.f('pk_setor_cobrador'))
    )

    with op.batch_alter_table('setor') as batch_op:
        batch_op.drop_constraint(op.f('uq_setor_nome'), type_='unique')
        batch_op.drop_column('cidade')
        batch_op.drop_column('uf')
        batch_op.add_column(sa.Column('cidade_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(op.f('fk_setor_cidade_id_cidade'), 'cidade', ['cidade_id'], ['id'])
        batch_op.create_index(op.f('ix_setor_cidade_id'), ['cidade_id'], unique=False)
        batch_op.create_unique_constraint(op.f('uq_setor_nome'), ['nome', 'cidade_id'])


def downgrade() -> None:
    with op.batch_alter_table('setor') as batch_op:
        batch_op.drop_constraint(op.f('uq_setor_nome'), type_='unique')
        batch_op.drop_index(op.f('ix_setor_cidade_id'))
        batch_op.drop_constraint(op.f('fk_setor_cidade_id_cidade'), type_='foreignkey')
        batch_op.drop_column('cidade_id')
        batch_op.add_column(sa.Column('cidade', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('uf', sa.String(length=2), nullable=True))
        batch_op.create_unique_constraint(op.f('uq_setor_nome'), ['nome', 'cidade'])

    op.drop_table('setor_cobrador')
    op.create_table('setor_cobrador',
    sa.Column('setor_id', sa.Integer(), nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('funcionario_id', sa.Integer(), nullable=False),
    *_datas(),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_setor_cobrador_empresa_id_empresa')),
    sa.ForeignKeyConstraint(['funcionario_id'], ['funcionario.id'],
                            name=op.f('fk_setor_cobrador_funcionario_id_funcionario')),
    sa.ForeignKeyConstraint(['setor_id'], ['setor.id'], name=op.f('fk_setor_cobrador_setor_id_setor'),
                            ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('setor_id', 'empresa_id', name=op.f('pk_setor_cobrador'))
    )
    op.drop_table('cobrador')
    op.drop_index(op.f('ix_cidade_nome_busca'), table_name='cidade')
    op.drop_table('cidade')
