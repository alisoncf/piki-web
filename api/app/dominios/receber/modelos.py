"""Contas a receber (D9, D26). No VB6: tab_doc e tab_itdoc (tipo R).

Por enquanto nascem só do crediário da venda: o que não foi pago na entrada vira
parcelas, impressas no carnê. A conta é da loja que vendeu, mas o limite do
cliente soma o que está em aberto em todas as lojas, e a parcela pode ser paga
em qualquer loja: o recebimento é da loja e do caixa de quem recebeu.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Usuario
from app.dominios.caixa.modelos import FormaPagamento, SessaoCaixa
from app.dominios.clientes.modelos import Cliente
from app.dominios.empresas.modelos import Empresa
from app.nucleo.banco import Base, ComDatas


# como o cliente vai pagar, escolhido por ele quando a venda é efetivada (tab_tipocob do VB6, pelo cod_tip)
TIPOS_COBRANCA = {
    "loja": ("Pagamento na loja", "1"),
    "cliente": ("Cobrança no cliente", "2"),
    "representante": ("Representante recebe", "3"),
    "deposito": ("Depósito bancário", "4"),
    "boleto": ("Boleto bancário", "5"),
}


class ContaCobranca(ComDatas, Base):
    """Onde o carnê está para ser cobrado (tab_contacob do VB6): na loja, sem estar com ninguém (a padrão, Geral),
    com um cobrador, com o advogado, num balanço... Uma lista só para todas as lojas, juntada pelo nome."""

    __tablename__ = "conta_cobranca"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(40), unique=True)
    padrao: Mapped[bool] = mapped_column(Boolean, server_default=false(), default=False)  # a Geral
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


# de onde veio a conta (esp_doc do VB6: V venda, A acerto de consignação, F e outros avulsos)
ORIGENS = {"venda": "Venda", "acerto": "Acerto de consignação", "avulso": "Avulsa"}


class ContaReceber(ComDatas, Base):
    """Um carnê: o valor a prazo de uma venda (ou de um acerto, ou avulso, vindos do VB6), dividido em parcelas.

    O número dos documentos do VB6 se repete entre as lojas: o da conta importada fica em documento_legado,
    e só identifica junto com a loja (empresa_id).
    """

    __tablename__ = "conta_receber"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)  # a loja que vendeu
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), index=True)
    venda_id: Mapped[int | None] = mapped_column(ForeignKey("venda.id"), unique=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # soma das parcelas
    historico: Mapped[str] = mapped_column(String(80))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))  # quem lançou (no VB6, pode faltar)
    origem: Mapped[str] = mapped_column(String(10), server_default="venda", default="venda")  # ver ORIGENS
    documento_legado: Mapped[str | None] = mapped_column(String(20))  # num_doc do VB6 (na venda, o num_ven)

    cliente: Mapped[Cliente] = relationship(lazy="joined")
    usuario: Mapped[Usuario | None] = relationship(lazy="joined")
    empresa: Mapped[Empresa] = relationship(lazy="joined")
    venda: Mapped["Venda | None"] = relationship()  # noqa: F821 (vendas.modelos); só quando pedida
    parcelas: Mapped[list["ParcelaReceber"]] = relationship(
        back_populates="conta", cascade="all, delete-orphan", order_by="ParcelaReceber.numero", lazy="selectin"
    )

    @property
    def documento(self) -> str:
        """Como a conta é chamada na tela: loja e número do VB6 (01-0001234) ou, nas novas, a venda ou o id."""
        if self.documento_legado:
            return f"{self.empresa.codigo}-{self.documento_legado}"
        if self.venda is not None:
            return f"{self.empresa.codigo}-venda {self.venda.numero}"
        return str(self.id)


class ParcelaReceber(Base):
    __tablename__ = "conta_receber_parcela"
    __table_args__ = (UniqueConstraint("conta_id", "numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conta_id: Mapped[int] = mapped_column(ForeignKey("conta_receber.id", ondelete="CASCADE"), index=True)
    numero: Mapped[int] = mapped_column(Integer)  # 1, 2, 3...
    vencimento: Mapped[date] = mapped_column(Date, index=True)
    # o vencimento com que a parcela nasceu (vencini_itd); o de cima muda quando é prorrogada
    vencimento_inicial: Mapped[date | None] = mapped_column(Date)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    aberto: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # o que falta pagar (reman_itd no VB6)
    conta_cobranca_id: Mapped[int] = mapped_column(ForeignKey("conta_cobranca.id"), index=True)
    tipo_cobranca: Mapped[str | None] = mapped_column(String(15))  # ver TIPOS_COBRANCA
    # prejuízo: a parcela que não se espera mais receber (o cliente morreu, não foi achado...). Sai da lista
    # do contas a receber, mas o cliente continua devendo: se pagar um dia, recebe normalmente.
    prejuizo_em: Mapped[datetime | None] = mapped_column(DateTime)
    prejuizo_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    prejuizo_motivo: Mapped[str | None] = mapped_column(String(200))

    conta: Mapped[ContaReceber] = relationship(back_populates="parcelas", lazy="selectin")
    prejuizo_por: Mapped[Usuario | None] = relationship(lazy="joined")
    conta_cobranca: Mapped[ContaCobranca] = relationship(lazy="joined")

    @property
    def prejuizo(self) -> bool:
        return self.prejuizo_em is not None


class RecebimentoCrediario(Base):
    """O cliente paga parcelas no caixa (de qualquer loja): quanto de cada uma, os juros e como pagou."""

    __tablename__ = "recebimento_crediario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)  # a loja que recebeu
    sessao_caixa_id: Mapped[int] = mapped_column(ForeignKey("caixa_sessao.id"), index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), index=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    valor_recebido: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))  # o que o cliente deu, no dinheiro
    estornado_em: Mapped[datetime | None] = mapped_column(DateTime)
    estornado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))

    empresa: Mapped[Empresa] = relationship(lazy="joined")
    sessao_caixa: Mapped[SessaoCaixa] = relationship(lazy="joined")
    cliente: Mapped[Cliente] = relationship(lazy="joined")
    usuario: Mapped[Usuario] = relationship(foreign_keys=[usuario_id], lazy="joined")
    estornado_por: Mapped[Usuario | None] = relationship(foreign_keys=[estornado_por_id], lazy="joined")
    itens: Mapped[list["ItemRecebimento"]] = relationship(
        back_populates="recebimento", cascade="all, delete-orphan", order_by="ItemRecebimento.id", lazy="selectin")
    pagamentos: Mapped[list["PagamentoRecebimento"]] = relationship(
        back_populates="recebimento", cascade="all, delete-orphan", order_by="PagamentoRecebimento.id", lazy="selectin")

    @property
    def total(self) -> Decimal:
        return sum((i.valor + i.juros for i in self.itens), Decimal("0.00"))

    @property
    def troco(self) -> Decimal | None:
        if self.valor_recebido is None:
            return None
        return self.valor_recebido - sum((p.valor for p in self.pagamentos if p.forma_pagamento.tipo == "dinheiro"),
                                         Decimal("0.00"))


class ItemRecebimento(Base):
    """Quanto foi pago de uma parcela (pode ser só uma parte) e os juros de atraso cobrados."""

    __tablename__ = "recebimento_crediario_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recebimento_id: Mapped[int] = mapped_column(ForeignKey("recebimento_crediario.id", ondelete="CASCADE"), index=True)
    parcela_id: Mapped[int] = mapped_column(ForeignKey("conta_receber_parcela.id"), index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # abatido do que falta pagar da parcela
    juros: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal(0))

    recebimento: Mapped[RecebimentoCrediario] = relationship(back_populates="itens")
    parcela: Mapped[ParcelaReceber] = relationship(lazy="joined")


class PagamentoRecebimento(Base):
    __tablename__ = "recebimento_crediario_pagamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recebimento_id: Mapped[int] = mapped_column(ForeignKey("recebimento_crediario.id", ondelete="CASCADE"), index=True)
    forma_pagamento_id: Mapped[int] = mapped_column(ForeignKey("forma_pagamento.id"))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    recebimento: Mapped[RecebimentoCrediario] = relationship(back_populates="pagamentos")
    forma_pagamento: Mapped[FormaPagamento] = relationship(lazy="joined")
