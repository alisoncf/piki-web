"""cadastro de empresas: esquema de cores, cidade do IBGE e imagens

- empresa ganha tema (JSON com principal, fundo e menu), no lugar do nome de
  cor da paleta fixa (D19); quem tinha cor escolhida fica com o esquema dela;
- a cidade passa a ser uma cidade do IBGE (cidade_id), no lugar da UF e do
  código do município soltos;
- empresa ganha suframa;
- empresa_imagem guarda o logo dos relatórios e o QR code do boleto.

Revisão: 0011
Anterior: 0010
Criada em: 2026-11-01
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0011'
down_revision: str | None = '0010'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# a paleta da migração 0003, para converter as cores já escolhidas
_PALETA = {
    "azul": "#2f6fb0", "laranja": "#d9822b", "verde-azulado": "#1f8a80", "roxo": "#6a4fc0",
    "oliva": "#7a862c", "marrom": "#8c5a3c", "ciano": "#2593b8", "ardosia": "#55708a",
}


def _misturar(cor: str, outra: str, proporcao: float) -> str:
    a = [int(cor[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(outra[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * proporcao + y * (1 - proporcao)):02x}" for x, y in zip(a, b))


def upgrade() -> None:
    with op.batch_alter_table('empresa') as batch_op:
        batch_op.add_column(sa.Column('suframa', sa.String(length=19), nullable=True))
        batch_op.add_column(sa.Column('cidade_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('tema', sa.JSON(), nullable=True))
        batch_op.create_foreign_key(op.f('fk_empresa_cidade_id_cidade'), 'cidade', ['cidade_id'], ['id'])
        batch_op.create_index(op.f('ix_empresa_cidade_id'), ['cidade_id'], unique=False)

    empresa = sa.table(
        'empresa', sa.column('id', sa.Integer), sa.column('cor', sa.String), sa.column('codigo_municipio', sa.String),
        sa.column('cidade_id', sa.Integer), sa.column('tema', sa.JSON),
    )
    cidade = sa.table('cidade', sa.column('id', sa.Integer), sa.column('codigo_ibge', sa.String))
    conexao = op.get_bind()
    for id_, cor, codigo_municipio in conexao.execute(sa.select(empresa.c.id, empresa.c.cor, empresa.c.codigo_municipio)):
        valores = {}
        if cor in _PALETA:
            principal = _PALETA[cor]
            valores['tema'] = {"principal": principal, "fundo": _misturar(principal, "#ffffff", 0.08),
                               "menu": _misturar(principal, "#1c1b1f", 0.15)}
        if codigo_municipio:
            valores['cidade_id'] = conexao.scalar(sa.select(cidade.c.id).where(cidade.c.codigo_ibge == codigo_municipio))
        if valores:
            conexao.execute(empresa.update().where(empresa.c.id == id_).values(**valores))

    with op.batch_alter_table('empresa') as batch_op:
        batch_op.drop_column('cor')
        batch_op.drop_column('uf')
        batch_op.drop_column('codigo_municipio')

    op.create_table(
        'empresa_imagem',
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=10), nullable=False),
        sa.Column('tipo_conteudo', sa.String(length=30), nullable=False),
        sa.Column('conteudo', sa.LargeBinary(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], name=op.f('fk_empresa_imagem_empresa_id_empresa'),
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('empresa_id', 'tipo', name=op.f('pk_empresa_imagem')),
    )


def downgrade() -> None:
    op.drop_table('empresa_imagem')
    with op.batch_alter_table('empresa') as batch_op:
        batch_op.add_column(sa.Column('codigo_municipio', sa.String(length=7), nullable=True))
        batch_op.add_column(sa.Column('uf', sa.String(length=2), nullable=True))
        batch_op.add_column(sa.Column('cor', sa.String(length=20), nullable=True))

    empresa = sa.table('empresa', sa.column('id', sa.Integer), sa.column('cidade_id', sa.Integer),
                       sa.column('codigo_municipio', sa.String), sa.column('uf', sa.String))
    cidade = sa.table('cidade', sa.column('id', sa.Integer), sa.column('codigo_ibge', sa.String), sa.column('uf', sa.String))
    conexao = op.get_bind()
    for id_, codigo_ibge, uf in conexao.execute(
        sa.select(empresa.c.id, cidade.c.codigo_ibge, cidade.c.uf).join(cidade, cidade.c.id == empresa.c.cidade_id)
    ):
        conexao.execute(empresa.update().where(empresa.c.id == id_).values(codigo_municipio=codigo_ibge, uf=uf))

    with op.batch_alter_table('empresa') as batch_op:
        batch_op.drop_index(op.f('ix_empresa_cidade_id'))
        batch_op.drop_constraint(op.f('fk_empresa_cidade_id_cidade'), type_='foreignkey')
        batch_op.drop_column('tema')
        batch_op.drop_column('cidade_id')
        batch_op.drop_column('suframa')
