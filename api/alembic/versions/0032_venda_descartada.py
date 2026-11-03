"""venda descartada (D26)

"Cancelada" fica só para a venda efetivada (recebida) que foi desfeita. A
aberta ou fechada em que o cliente desistiu passa a ser "descartada": as que
já estavam canceladas sem terem sido recebidas mudam para descartada.

Revisão: 0032
Anterior: 0031
Criada em: 2026-11-03
"""
from collections.abc import Sequence

from alembic import op


revision: str = '0032'
down_revision: str | None = '0031'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("update venda set situacao = 'descartada' where situacao = 'cancelada' and recebida_em is null")


def downgrade() -> None:
    op.execute("update venda set situacao = 'cancelada' where situacao = 'descartada'")
