"""Financeiro: o plano de contas (tab_planocontas do VB6), uma lista só para todas as lojas.

Diz para onde foi (despesa) ou de onde veio (receita) o dinheiro, para os relatórios:
"Despesa → Combustíveis". É diferente do motivo do lançamento do caixa, que é fixo e diz
que operação é (troco, despesa, vale...). Cadastrável pelas lojas.
"""
from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base, ComDatas

TIPOS = {"receita": "Receita", "despesa": "Despesa"}


class ContaPlano(ComDatas, Base):
    __tablename__ = "plano_conta"
    __table_args__ = (UniqueConstraint("tipo", "nome"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10))  # ver TIPOS
    nome: Mapped[str] = mapped_column(String(60))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
