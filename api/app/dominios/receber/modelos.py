"""Contas a receber (D9, D26). No VB6: tab_doc e tab_itdoc (tipo R).

Por enquanto nascem só do crediário da venda: o que não foi pago na entrada vira
parcelas, impressas no carnê. A conta é da loja que vendeu, mas o limite do
cliente soma o que está em aberto em todas as lojas. A baixa das parcelas (com
os juros de atraso) vem depois.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Usuario
from app.dominios.clientes.modelos import Cliente
from app.nucleo.banco import Base, ComDatas


class ContaReceber(ComDatas, Base):
    """Um carnê: o valor a prazo de uma venda, dividido em parcelas."""

    __tablename__ = "conta_receber"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)  # a loja que vendeu
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), index=True)
    venda_id: Mapped[int | None] = mapped_column(ForeignKey("venda.id"), unique=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # soma das parcelas
    historico: Mapped[str] = mapped_column(String(80))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))  # quem lançou

    cliente: Mapped[Cliente] = relationship(lazy="joined")
    usuario: Mapped[Usuario] = relationship(lazy="joined")
    parcelas: Mapped[list["ParcelaReceber"]] = relationship(
        back_populates="conta", cascade="all, delete-orphan", order_by="ParcelaReceber.numero", lazy="selectin"
    )


class ParcelaReceber(Base):
    __tablename__ = "conta_receber_parcela"
    __table_args__ = (UniqueConstraint("conta_id", "numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conta_id: Mapped[int] = mapped_column(ForeignKey("conta_receber.id", ondelete="CASCADE"), index=True)
    numero: Mapped[int] = mapped_column(Integer)  # 1, 2, 3...
    vencimento: Mapped[date] = mapped_column(Date, index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    aberto: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # o que falta pagar (reman_itd no VB6)

    conta: Mapped[ContaReceber] = relationship(back_populates="parcelas")
