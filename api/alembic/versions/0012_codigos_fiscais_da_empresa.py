"""códigos fiscais da empresa fora do padrão viram vazio

Nos bancos das lojas o ind_perfil da sped_empresa está '1', que não é perfil
do SPED (A, B ou C), e a ficha da empresa não abria. O ETL agora descarta
códigos fora do padrão; esta migração limpa o que já foi importado.

Revisão: 0012
Anterior: 0011
Criada em: 2026-11-01
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0012'
down_revision: str | None = '0011'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_VALIDOS = {'crt': ['1', '2', '3'], 'sped_perfil': ['A', 'B', 'C'], 'sped_atividade': ['0', '1']}


def upgrade() -> None:
    empresa = sa.table('empresa', *(sa.column(c, sa.String) for c in _VALIDOS))
    for coluna, validos in _VALIDOS.items():
        op.execute(empresa.update().where(empresa.c[coluna].not_in(validos)).values({coluna: None}))


def downgrade() -> None:
    pass  # os códigos descartados não tinham uso
