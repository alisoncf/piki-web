"""Notas fiscais (D29): NFC-e (modelo 65) e NF-e (modelo 55), emitidas pela própria API.

Por enquanto só a numeração: o último número usado em cada modelo e série da loja.
A série é a do caixa (101 é o caixa 01, como no VB6). Na virada da loja, a numeração
continua de onde o VB6 parou (python -m etl notas).
"""
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base, ComDatas

MODELOS = {"65": "NFC-e", "55": "NF-e"}


class NumeracaoNota(ComDatas, Base):
    __tablename__ = "nota_numeracao"
    __table_args__ = (UniqueConstraint("empresa_id", "modelo", "serie"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    modelo: Mapped[str] = mapped_column(String(2))  # ver MODELOS
    serie: Mapped[int] = mapped_column(Integer)
    ultimo: Mapped[int] = mapped_column(Integer, default=0)  # o último número usado
