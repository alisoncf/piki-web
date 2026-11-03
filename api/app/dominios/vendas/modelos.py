"""Vendas da loja (D26). No VB6: tab_vendas e tab_itvendas.

O vendedor monta a venda no balcão e a fecha com o cliente; o caixa recebe a
venda fechada, procurando pelo nome de quem comprou. O desconto é guardado em
cada item: o dado no total é rateado entre os itens (menos os em queima, que não
têm desconto), e cada item diz por quanto foi vendido de fato. A venda aberta ou
fechada vence em 10 dias.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Usuario
from app.dominios.caixa.modelos import FormaPagamento, SessaoCaixa
from app.dominios.cidades.modelos import Cidade
from app.dominios.clientes.modelos import Cliente
from app.dominios.produtos.modelos import Produto
from app.nucleo.banco import Base, ComDatas

ABERTA = "aberta"  # o vendedor está montando
FECHADA = "fechada"  # o vendedor fechou com o cliente; espera o caixa
RECEBIDA = "recebida"
CANCELADA = "cancelada"
VENCIDA = "vencida"
SITUACOES = {ABERTA: "Aberta", FECHADA: "Fechada", RECEBIDA: "Recebida", CANCELADA: "Cancelada", VENCIDA: "Vencida"}

DIAS_PARA_VENCER = 10
# a venda recebida só pode ser cancelada nestes dias depois de recebida (o Alison pediu um prazo curto)
DIAS_PARA_CANCELAR = 7


class Consumidor(ComDatas, Base):
    """Quem compra sem ser cliente cadastrado (o cliente 0 do VB6): um cadastro curto, para identificar e contatar.

    Entra quando a venda traz o CPF, o telefone, o e-mail ou o aniversário; só com o nome, fica só na venda. O CPF identifica
    quem já comprou antes.
    """

    __tablename__ = "consumidor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(60))
    cpf: Mapped[str | None] = mapped_column(String(11), unique=True)
    dia_nascimento: Mapped[int | None] = mapped_column(SmallInteger)
    mes_nascimento: Mapped[int | None] = mapped_column(SmallInteger)
    telefone: Mapped[str | None] = mapped_column(String(15))
    email: Mapped[str | None] = mapped_column(String(100))


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
    consumidor_id: Mapped[int | None] = mapped_column(ForeignKey("consumidor.id"), index=True)
    # nome de quem comprou, pelo qual o caixa acha a venda: o do cliente cadastrado ou o que o vendedor digitou
    comprador: Mapped[str | None] = mapped_column(String(60), index=True)
    forma_pagamento_id: Mapped[int | None] = mapped_column(ForeignKey("forma_pagamento.id"))
    parcelas: Mapped[int] = mapped_column(Integer, default=1)
    # % aplicado aos itens que entrarem depois: o da forma ou o último dado no total
    percentual_desconto: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal(0))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal(0))  # itens a preço de tabela
    desconto: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal(0))  # soma dos descontos dos itens
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal(0))  # itens com desconto + entrega
    # quem autorizou o desconto acima do limite do vendedor e as parcelas acima do limite da forma
    desconto_autorizado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    parcelas_autorizadas_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    observacao: Mapped[str | None] = mapped_column(String(200))
    fechada_em: Mapped[datetime | None] = mapped_column(DateTime)
    # recebimento no caixa
    sessao_caixa_id: Mapped[int | None] = mapped_column(ForeignKey("caixa_sessao.id"), index=True)
    recebida_em: Mapped[datetime | None] = mapped_column(DateTime)
    recebida_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    valor_recebido: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))  # o que o cliente deu, no dinheiro
    # crediário: a data de onde contam os vencimentos (a 1ª parcela vence um intervalo depois)
    data_base: Mapped[date | None] = mapped_column(Date)
    modelo_nota: Mapped[str] = mapped_column(String(2), server_default="65", default="65")  # 65 NFC-e, 55 NF-e
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
    consumidor: Mapped[Consumidor | None] = relationship(lazy="joined")
    entrega: Mapped["EntregaVenda | None"] = relationship(
        back_populates="venda", cascade="all, delete-orphan", lazy="joined")
    forma_pagamento: Mapped[FormaPagamento | None] = relationship(foreign_keys=[forma_pagamento_id], lazy="joined")
    pagamentos: Mapped[list["PagamentoVenda"]] = relationship(
        back_populates="venda", cascade="all, delete-orphan", order_by="PagamentoVenda.ordem", lazy="selectin")
    desconto_autorizado_por: Mapped[Usuario | None] = relationship(foreign_keys=[desconto_autorizado_por_id], lazy="joined")
    parcelas_autorizadas_por: Mapped[Usuario | None] = relationship(
        foreign_keys=[parcelas_autorizadas_por_id], lazy="joined")
    sessao_caixa: Mapped[SessaoCaixa | None] = relationship(lazy="joined")
    recebida_por: Mapped[Usuario | None] = relationship(foreign_keys=[recebida_por_id], lazy="joined")
    cancelada_por: Mapped[Usuario | None] = relationship(foreign_keys=[cancelada_por_id], lazy="joined")
    limite_autorizado_por: Mapped[Usuario | None] = relationship(foreign_keys=[limite_autorizado_por_id], lazy="joined")

    @property
    def taxa_entrega(self) -> Decimal:
        return self.entrega.taxa if self.entrega else Decimal("0.00")

    @property
    def pago_na_hora(self) -> Decimal:
        """O que o cliente pagou no caixa (no crediário, a entrada; o resto é o carnê)."""
        return sum((p.valor for p in self.pagamentos), Decimal("0.00"))

    @property
    def a_prazo(self) -> Decimal:
        return self.total - self.pago_na_hora if self.situacao == "recebida" else Decimal("0.00")

    @property
    def troco(self) -> Decimal | None:
        """Só do dinheiro: o que o cliente deu menos o que ficou no dinheiro."""
        if self.valor_recebido is None:
            return None
        return self.valor_recebido - sum((p.valor for p in self.pagamentos if p.forma_pagamento.tipo == "dinheiro"),
                                         Decimal("0.00"))


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
    # vendido pelo preço de queima: não tem desconto
    em_queima: Mapped[bool] = mapped_column(Boolean, server_default=false(), default=False)

    venda: Mapped[Venda] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship(lazy="joined")

    @property
    def bruto(self) -> Decimal:
        return (self.quantidade * self.preco).quantize(Decimal("0.01"))


class EntregaVenda(Base):
    """Venda com entrega: a taxa (entra no total, sem desconto) e o endereço."""

    __tablename__ = "venda_entrega"

    venda_id: Mapped[int] = mapped_column(ForeignKey("venda.id", ondelete="CASCADE"), primary_key=True)
    taxa: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal(0))
    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None] = mapped_column(String(100))
    numero: Mapped[str | None] = mapped_column(String(20))
    complemento: Mapped[str | None] = mapped_column(String(60))
    bairro: Mapped[str | None] = mapped_column(String(60))
    cidade_id: Mapped[int | None] = mapped_column(ForeignKey("cidade.id"))
    ponto_referencia: Mapped[str | None] = mapped_column(String(60))
    telefone: Mapped[str | None] = mapped_column(String(15))  # de quem recebe

    venda: Mapped[Venda] = relationship(back_populates="entrega")
    cidade: Mapped[Cidade | None] = relationship(lazy="joined")


class PagamentoVenda(Base):
    """Uma parte do que foi pago no caixa: um pouco no PIX, um pouco no cartão... (no crediário, a entrada)."""

    __tablename__ = "venda_pagamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("venda.id", ondelete="CASCADE"), index=True)
    ordem: Mapped[int] = mapped_column(Integer)
    forma_pagamento_id: Mapped[int] = mapped_column(ForeignKey("forma_pagamento.id"))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    parcelas: Mapped[int] = mapped_column(Integer, default=1)  # no cartão de crédito

    venda: Mapped[Venda] = relationship(back_populates="pagamentos")
    forma_pagamento: Mapped[FormaPagamento] = relationship(lazy="joined")
