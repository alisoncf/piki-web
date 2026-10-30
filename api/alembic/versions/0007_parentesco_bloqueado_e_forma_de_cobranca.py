"""parentesco, cliente bloqueado e forma de cobranca por nome

- cliente.situacao ('1' liberado, '2' bloqueado) vira cliente.bloqueado;
- cliente.forma_cobranca passa dos códigos do VB6 (1, 2, 3) para nomes
  (domicilio, trabalho, loja);
- o tipo da referência vira a tabela parentesco, que já nasce com a lista
  do VB6 (tab_tipopar, igual em todas as lojas).

Revisão: 0007
Anterior: 0006
Criada em: 2026-10-30
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0007'
down_revision: str | None = '0006'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# cod_tip da tab_tipopar → nome
_PARENTESCOS = {
    '0': 'Outro', '1': 'Cônjuge', '2': 'Filhos', '3': 'Pais', '4': 'Irmão',
    '5': 'Namorado(a)', '6': 'Amigo', '7': 'Primo', '8': 'Sobrinho', '9': 'Tio',
}
_COBRANCA = {'1': 'domicilio', '2': 'trabalho', '3': 'loja'}


def upgrade() -> None:
    parentesco = op.create_table('parentesco',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=30), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_parentesco')),
    sa.UniqueConstraint('nome', name=op.f('uq_parentesco_nome'))
    )
    op.bulk_insert(parentesco, [{'nome': nome, 'ativo': True} for nome in _PARENTESCOS.values()])

    with op.batch_alter_table('cliente') as batch_op:
        batch_op.add_column(sa.Column('bloqueado', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.alter_column('forma_cobranca', existing_type=sa.String(length=1), type_=sa.String(length=10),
                              existing_nullable=False)
    op.execute("UPDATE cliente SET bloqueado = (situacao = '2')")
    for codigo, nome in _COBRANCA.items():
        op.execute(f"UPDATE cliente SET forma_cobranca = '{nome}' WHERE forma_cobranca = '{codigo}'")
    with op.batch_alter_table('cliente') as batch_op:
        batch_op.drop_column('situacao')
        batch_op.alter_column('bloqueado', existing_type=sa.Boolean(), server_default=None, existing_nullable=False)

    with op.batch_alter_table('cliente_referencia') as batch_op:
        batch_op.add_column(sa.Column('parentesco_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(op.f('fk_cliente_referencia_parentesco_id_parentesco'), 'parentesco',
                                    ['parentesco_id'], ['id'])
    for codigo, nome in _PARENTESCOS.items():
        op.execute(f"UPDATE cliente_referencia SET parentesco_id = (SELECT id FROM parentesco WHERE nome = '{nome}') "
                   f"WHERE tipo = '{codigo}'")
    with op.batch_alter_table('cliente_referencia') as batch_op:
        batch_op.drop_column('tipo')


def downgrade() -> None:
    with op.batch_alter_table('cliente_referencia') as batch_op:
        batch_op.add_column(sa.Column('tipo', sa.String(length=2), nullable=True))
    for codigo, nome in _PARENTESCOS.items():
        op.execute(f"UPDATE cliente_referencia SET tipo = '{codigo}' "
                   f"WHERE parentesco_id = (SELECT id FROM parentesco WHERE nome = '{nome}')")
    with op.batch_alter_table('cliente_referencia') as batch_op:
        batch_op.drop_constraint(op.f('fk_cliente_referencia_parentesco_id_parentesco'), type_='foreignkey')
        batch_op.drop_column('parentesco_id')

    with op.batch_alter_table('cliente') as batch_op:
        batch_op.add_column(sa.Column('situacao', sa.String(length=1), nullable=False, server_default='1'))
    op.execute("UPDATE cliente SET situacao = CASE WHEN bloqueado THEN '2' ELSE '1' END")
    for codigo, nome in _COBRANCA.items():
        op.execute(f"UPDATE cliente SET forma_cobranca = '{codigo}' WHERE forma_cobranca = '{nome}'")
    with op.batch_alter_table('cliente') as batch_op:
        batch_op.alter_column('situacao', existing_type=sa.String(length=1), server_default=None,
                              existing_nullable=False)
        batch_op.alter_column('forma_cobranca', existing_type=sa.String(length=10), type_=sa.String(length=1),
                              existing_nullable=False)
        batch_op.drop_column('bloqueado')
    op.drop_table('parentesco')
