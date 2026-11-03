"""Estoque de cada loja (D24). No VB6: ef_pro (o fiscal, que passa a ser o real), r_pro e endereco_pro da tab_produtos.

O saldo fica na linha do produto na loja, e cada mudança fica registrada num
movimento, com o saldo depois dele: o histórico sempre explica o saldo.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Usuario
from app.nucleo.banco import Base, ComDatas


class Estoque(ComDatas, Base):
    """O produto numa loja. Sem linha, o saldo é zero."""

    __tablename__ = "estoque"
    __table_args__ = (UniqueConstraint("empresa_id", "produto_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"), index=True)
    # tudo o que é da loja, inclusive o que está com os representantes
    quantidade: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    # o que está com os representantes (consignação): faz parte da quantidade, mas não está na loja
    reservado: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    localizacao: Mapped[str | None] = mapped_column(String(30))  # prateleira, depósito...

    # impostos que dependem do regime da empresa (os do produto ficam no produto)
    cst_csosn: Mapped[str | None] = mapped_column(String(3))  # CST (regime normal) ou CSOSN (Simples) do ICMS
    cfop: Mapped[str | None] = mapped_column(String(4))  # da venda dentro do estado
    aliquota_icms: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    @property
    def disponivel(self) -> Decimal:
        """O que está na loja para vender."""
        zero = Decimal("0.000")
        return (zero if self.quantidade is None else self.quantidade) - (zero if self.reservado is None else self.reservado)


# tipos de movimento; os de venda, entrada e consignação serão gravados pelas telas desses assuntos
TIPOS = {
    "importacao": "Saldo do VB6",
    "ajuste": "Ajuste",
    "inventario": "Inventário",
    "venda": "Venda",
    "devolucao_venda": "Devolução de venda",
    "cancelamento_venda": "Cancelamento de venda",
    "entrada": "Entrada",
    "consignacao_envio": "Envio ao representante",
    "consignacao_devolucao": "Devolução do representante",
    "consignacao_acerto": "Acerto de consignação",
}


class MovimentoEstoque(Base):
    """Uma mudança no estoque de um produto numa loja: venda, entrada, consignação, ajuste..."""

    __tablename__ = "estoque_movimento"
    __table_args__ = (Index("ix_estoque_movimento_produto", "empresa_id", "produto_id", "id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"), index=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    tipo: Mapped[str] = mapped_column(String(30))  # ver TIPOS
    # quanto mudou (negativo = saiu) e como ficou depois
    quantidade: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    reservado: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    saldo: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    saldo_reservado: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    # o que originou: "venda 1234", "nota 5678"... (vazio no ajuste)
    documento: Mapped[str | None] = mapped_column(String(40))
    observacao: Mapped[str | None] = mapped_column(String(200))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))

    usuario: Mapped[Usuario | None] = relationship(lazy="joined")

    @property
    def descricao(self) -> str:
        return TIPOS.get(self.tipo, self.tipo)
