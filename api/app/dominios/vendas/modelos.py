"""Vendas da loja (D26). No VB6: tab_vendas e tab_itvendas.

O vendedor monta a venda no balcão e o caixa recebe. O desconto é guardado em
cada item: o dado no total é rateado entre os itens, e cada item diz por quanto
foi vendido de fato. A venda aberta vence em 10 dias.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Usuario
from app.dominios.caixa.modelos import FormaPagamento, SessaoCaixa
from app.dominios.clientes.modelos import Cliente
from app.dominios.produtos.modelos import Produto
from app.nucleo.banco import Base, ComDatas

ABERTA = "aberta"
RECEBIDA = "recebida"
CANCELADA = "cancelada"
VENCIDA = "vencida"
SITUACOES = {ABERTA: "Aberta", RECEBIDA: "Recebida", CANCELADA: "Cancelada", VENCIDA: "Vencida"}

DIAS_PARA_VENCER = 10


class Venda(ComDatas, Base):
    __tablename__ = "venda"
    __table_args__ = (UniqueConstraint("empresa_id", "numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)  # sequência da loja
    situacao: Mapped[str] = mapped_column(String(10), default=ABERTA, index=True)
    vendedor_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))  # quem montou
    vence_em: Mapped[datetime] = mapped_column(DateTime)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("cliente.id"), index=True)
    forma_pagamento_id: Mapped[int | None] = mapped_column(ForeignKey("forma_pagamento.id"))
    parcelas: Mapped[int] = mapped_column(Integer, default=1)
    # % aplicado aos itens que entrarem depois: o da forma ou o último dado no total
    percentual_desconto: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal(0))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal(0))  # itens a preço de tabela
    desconto: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal(0))  # soma dos descontos dos itens
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal(0))
    # quem autorizou o desconto acima do limite do vendedor e as parcelas acima do limite da forma
    desconto_autorizado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    parcelas_autorizadas_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    observacao: Mapped[str | None] = mapped_column(String(200))
    # recebimento no caixa
    sessao_caixa_id: Mapped[int | None] = mapped_column(ForeignKey("caixa_sessao.id"), index=True)
    recebida_em: Mapped[datetime | None] = mapped_column(DateTime)
    recebida_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    valor_recebido: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))  # o que o cliente deu, no dinheiro
    # no crediário: o que foi pago na hora, em outra forma; o resto vira o carnê
    entrada: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    forma_entrada_id: Mapped[int | None] = mapped_column(ForeignKey("forma_pagamento.id"))
    # quem autorizou o crediário acima do limite disponível do cliente
    limite_autorizado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    cancelada_em: Mapped[datetime | None] = mapped_column(DateTime)
    cancelada_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(200))

    itens: Mapped[list["ItemVenda"]] = relationship(
        back_populates="venda", cascade="all, delete-orphan", order_by="ItemVenda.ordem", lazy="selectin"
    )
    vendedor: Mapped[Usuario] = relationship(foreign_keys=[vendedor_id], lazy="joined")
    cliente: Mapped[Cliente | None] = relationship(lazy="joined")
    forma_pagamento: Mapped[FormaPagamento | None] = relationship(foreign_keys=[forma_pagamento_id], lazy="joined")
    forma_entrada: Mapped[FormaPagamento | None] = relationship(foreign_keys=[forma_entrada_id], lazy="joined")
    desconto_autorizado_por: Mapped[Usuario | None] = relationship(foreign_keys=[desconto_autorizado_por_id], lazy="joined")
    parcelas_autorizadas_por: Mapped[Usuario | None] = relationship(
        foreign_keys=[parcelas_autorizadas_por_id], lazy="joined")
    sessao_caixa: Mapped[SessaoCaixa | None] = relationship(lazy="joined")
    recebida_por: Mapped[Usuario | None] = relationship(foreign_keys=[recebida_por_id], lazy="joined")
    cancelada_por: Mapped[Usuario | None] = relationship(foreign_keys=[cancelada_por_id], lazy="joined")
    limite_autorizado_por: Mapped[Usuario | None] = relationship(foreign_keys=[limite_autorizado_por_id], lazy="joined")

    @property
    def pago_na_hora(self) -> Decimal:
        """No crediário, só a entrada; nas outras formas, o total."""
        return self.total if self.entrada is None else self.entrada

    @property
    def troco(self) -> Decimal | None:
        return None if self.valor_recebido is None else self.valor_recebido - self.pago_na_hora


class ItemVenda(Base):
    """Um produto da venda: o preço de tabela, o desconto que coube a ele e por quanto saiu."""

    __tablename__ = "venda_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("venda.id", ondelete="CASCADE"), index=True)
    ordem: Mapped[int] = mapped_column(Integer)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"), index=True)
    descricao: Mapped[str] = mapped_column(String(120))  # o nome do produto na hora da venda
    quantidade: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    preco: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # unitário, de tabela
    desconto: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal(0))  # em reais, no item todo
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # por quanto foi vendido

    venda: Mapped[Venda] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship(lazy="joined")

    @property
    def bruto(self) -> Decimal:
        return (self.quantidade * self.preco).quantize(Decimal("0.01"))
