"""Consignação (D30): os representantes, que levam mercadoria da loja e acertam o que venderam.

O representante é um cliente especializado (Alison, 03/11/2026): os dados pessoais, o
endereço e os telefones são os da ficha do cliente; aqui ficam só os do consignado
(limite, situação, senha, comissões, avalista). Cadastro global, como o cliente; hoje só a
matriz trabalha com consignado. No VB6: tab_representantes, tab_reptip.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Usuario
from app.dominios.caixa.modelos import FormaPagamento
from app.dominios.clientes.modelos import Cliente
from app.dominios.produtos.modelos import Produto
from app.nucleo.banco import Base, ComDatas

# a comissão de quem não tem uma própria, por tipo de cobrança (tab_tipocob do VB6)
COMISSOES_PADRAO = {
    "loja": Decimal("20.00"),
    "cliente": Decimal("15.00"),
    "representante": Decimal("20.00"),
    "deposito": Decimal("0.00"),
    "boleto": Decimal("0.00"),
}

# no acerto à vista, que só o próprio representante faz, a comissão (o desconto dele) vai pelo jeito que ele paga;
# no de queima, é fixa (no VB6: o txdescontoavista_par, 20 e 15 no código, e 5 na queima)
COMISSOES_ACERTO = {
    "vista_dinheiro": ("Acerto à vista: dinheiro ou PIX", Decimal("25.00")),
    "vista_cartao": ("Acerto à vista: cartão à vista", Decimal("20.00")),
    "vista_parcelado": ("Acerto à vista: cartão parcelado", Decimal("15.00")),
    "queima": ("Acerto de queima", Decimal("5.00")),
}
COMISSOES_PADRAO |= {tipo: padrao for tipo, (_, padrao) in COMISSOES_ACERTO.items()}


class Representante(ComDatas, Base):
    __tablename__ = "representante"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[int] = mapped_column(Integer, unique=True)  # o cod_rep do VB6; os novos seguem a sequência
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)  # o excluído do VB6 fica inativo, para o histórico
    # bloqueado não leva mercadoria nem acerta para si a prazo; devolve e acerta para os clientes dele
    bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)
    motivo_bloqueio: Mapped[str | None] = mapped_column(Text)
    limite: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))  # pelo preço da transferência
    senha_hash: Mapped[str | None] = mapped_column(String(200))  # confirma a transferência no balcão
    bloqueia_impressao: Mapped[bool] = mapped_column(Boolean, default=False)
    bloqueia_devolucao: Mapped[bool] = mapped_column(Boolean, default=False)
    lembrete: Mapped[str | None] = mapped_column(Text)
    lembrete_acerto: Mapped[str | None] = mapped_column(Text)
    observacao: Mapped[str | None] = mapped_column(Text)
    ultima_conferencia: Mapped[date | None] = mapped_column(Date)
    data_cadastro: Mapped[date] = mapped_column(Date, default=date.today)

    avalista_nome: Mapped[str | None] = mapped_column(String(100))
    avalista_cpf: Mapped[str | None] = mapped_column(String(11))
    avalista_rg: Mapped[str | None] = mapped_column(String(20))
    avalista_endereco: Mapped[str | None] = mapped_column(String(200))
    avalista_telefones: Mapped[str | None] = mapped_column(String(200))
    avalista_anotacoes: Mapped[str | None] = mapped_column(Text)

    cliente: Mapped[Cliente] = relationship(lazy="joined")
    comissoes: Mapped[list["ComissaoRepresentante"]] = relationship(
        back_populates="representante", cascade="all, delete-orphan", lazy="selectin")

    def comissao(self, tipo_cobranca: str) -> Decimal:
        """A comissão do representante neste tipo de cobrança: a dele, ou a padrão."""
        propria = next((c.percentual for c in self.comissoes if c.tipo_cobranca == tipo_cobranca), None)
        return COMISSOES_PADRAO.get(tipo_cobranca, Decimal("0.00")) if propria is None else propria


class ComissaoRepresentante(Base):
    """A comissão própria do representante num tipo de cobrança (sem linha, vale a padrão)."""

    __tablename__ = "representante_comissao"

    representante_id: Mapped[int] = mapped_column(ForeignKey("representante.id", ondelete="CASCADE"), primary_key=True)
    tipo_cobranca: Mapped[str] = mapped_column(String(15), primary_key=True)  # ver TIPOS_COBRANCA (receber)
    percentual: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    representante: Mapped[Representante] = relationship(back_populates="comissoes")


# a transferência: montada no balcão (aberta) e confirmada pelo representante com a senha
ABERTA = "aberta"
CONFIRMADA = "confirmada"
SITUACOES_TRANSFERENCIA = (ABERTA, CONFIRMADA)


class Transferencia(ComDatas, Base):
    """O representante leva produtos "emprestados" para o estoque dele (tab_consignacoes do VB6, que não tinha
    cabeçalho: cada linha era um item). Uma aberta por representante; confirmada, os produtos passam a estar com
    ele (o reservado do estoque da loja) e cada item guarda quanto ainda resta com ele."""

    __tablename__ = "consignacao_transferencia"
    __table_args__ = (UniqueConstraint("empresa_id", "numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)  # sequência da loja
    representante_id: Mapped[int] = mapped_column(ForeignKey("representante.id"), index=True)
    situacao: Mapped[str] = mapped_column(String(10), default=ABERTA, index=True)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))  # pelo preço da transferência
    atendida_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))  # o funcionário do balcão
    confirmada_em: Mapped[datetime | None] = mapped_column(DateTime)

    representante: Mapped[Representante] = relationship(lazy="joined")
    atendida_por: Mapped[Usuario] = relationship(lazy="joined")
    itens: Mapped[list["ItemTransferencia"]] = relationship(
        back_populates="transferencia", cascade="all, delete-orphan", order_by="ItemTransferencia.ordem", lazy="selectin")


class ItemTransferencia(Base):
    __tablename__ = "consignacao_transferencia_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transferencia_id: Mapped[int] = mapped_column(ForeignKey("consignacao_transferencia.id", ondelete="CASCADE"),
                                                  index=True)
    ordem: Mapped[int] = mapped_column(Integer)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"), index=True)
    descricao: Mapped[str] = mapped_column(String(120))
    quantidade: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    preco: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # o preço de venda do dia, com que a peça sai
    # o que ainda está com o representante (o "reman." do VB6): baixa na devolução e no acerto
    restante: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=Decimal("0.000"))

    transferencia: Mapped[Transferencia] = relationship(back_populates="itens")
    produto: Mapped[Produto] = relationship(lazy="joined")

    @property
    def total(self) -> Decimal:
        return (self.quantidade * self.preco).quantize(Decimal("0.01"))



class Devolucao(ComDatas, Base):
    """O representante devolve produtos à loja, sem custo: sai de cada item de transferência escolhido (de onde a
    peça veio) e volta para a loja. Uma aberta por representante; confirmada com a senha dele. A retificadora
    corrige um produto transferido errado (tab_devconsign do VB6, com o retif_dev)."""

    __tablename__ = "consignacao_devolucao"
    __table_args__ = (UniqueConstraint("empresa_id", "numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)  # sequência da loja
    representante_id: Mapped[int] = mapped_column(ForeignKey("representante.id"), index=True)
    situacao: Mapped[str] = mapped_column(String(10), default=ABERTA, index=True)
    retificadora: Mapped[bool] = mapped_column(Boolean, default=False)
    observacao: Mapped[str | None] = mapped_column(String(200))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))  # pelo preço da transferência
    atendida_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    # o gerente que liberou, quando o representante tem a devolução bloqueada
    autorizada_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    confirmada_em: Mapped[datetime | None] = mapped_column(DateTime)

    representante: Mapped[Representante] = relationship(lazy="joined")
    atendida_por: Mapped[Usuario] = relationship(foreign_keys=[atendida_por_id], lazy="joined")
    autorizada_por: Mapped[Usuario | None] = relationship(foreign_keys=[autorizada_por_id], lazy="joined")
    itens: Mapped[list["ItemDevolucao"]] = relationship(
        back_populates="devolucao", cascade="all, delete-orphan", order_by="ItemDevolucao.ordem", lazy="selectin")


class ItemDevolucao(Base):
    __tablename__ = "consignacao_devolucao_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    devolucao_id: Mapped[int] = mapped_column(ForeignKey("consignacao_devolucao.id", ondelete="CASCADE"), index=True)
    ordem: Mapped[int] = mapped_column(Integer)
    # de que item de transferência a peça volta (o mesmo produto pode ter vindo em transferências diferentes)
    item_transferencia_id: Mapped[int] = mapped_column(ForeignKey("consignacao_transferencia_item.id"), index=True)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(14, 3))

    devolucao: Mapped[Devolucao] = relationship(back_populates="itens")
    item_transferencia: Mapped[ItemTransferencia] = relationship(lazy="joined")

    @property
    def total(self) -> Decimal:
        return (self.quantidade * self.item_transferencia.preco).quantize(Decimal("0.01"))


# o acerto: as peças que o representante vendeu saem do que está com ele e viram dinheiro ou carnê
PARA_CLIENTE = "cliente"  # o carnê no nome do cliente dele, que comprou; a comissão sai conforme o cliente paga
PARA_REPRESENTANTE = "representante"  # ele assume a dívida, como se tivesse comprado: a comissão vira desconto
A_PRAZO = "prazo"
A_VISTA = "vista"  # só para o próprio representante


class Acerto(ComDatas, Base):
    """O acerto do que o representante vendeu (tab_acertos e tab_itacertos do VB6). Montado no balcão (aberto) e
    confirmado no caixa do consignado; não pede a senha do representante.

    comissão = % × o total pelo preço da transferência (ou de queima) + a diferença (o que ele vendeu a mais).
    Para o cliente, o valor é o negociado (o total + a diferença); para o próprio representante, o negociado menos
    a comissão.
    """

    __tablename__ = "consignacao_acerto"
    __table_args__ = (UniqueConstraint("empresa_id", "numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    numero: Mapped[int] = mapped_column(Integer)  # sequência da loja
    representante_id: Mapped[int] = mapped_column(ForeignKey("representante.id"), index=True)
    situacao: Mapped[str] = mapped_column(String(10), default=ABERTA, index=True)
    para: Mapped[str] = mapped_column(String(13), default=PARA_CLIENTE)
    # de quem é o carnê: o cliente do representante, ou a ficha de cliente dele mesmo
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("cliente.id"), index=True)
    queima: Mapped[bool] = mapped_column(Boolean, default=False)  # só produtos em queima, pelo preço de queima
    pagamento: Mapped[str] = mapped_column(String(5), default=A_PRAZO)
    # o tipo de cobrança (a prazo), o jeito de pagar (à vista) ou a queima: diz o % da comissão
    tipo_comissao: Mapped[str] = mapped_column(String(15))
    percentual: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    total_inicial: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    diferenca: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))  # negociado − inicial
    comissao: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))  # o que se cobra
    parcelas: Mapped[int] = mapped_column(Integer, default=1)
    primeiro_vencimento: Mapped[date | None] = mapped_column(Date)
    atendida_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    # a gerência, quando o carnê passa do limite de crédito do cliente
    autorizada_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    sessao_caixa_id: Mapped[int | None] = mapped_column(ForeignKey("caixa_sessao.id"), index=True)
    confirmada_em: Mapped[datetime | None] = mapped_column(DateTime)

    representante: Mapped[Representante] = relationship(lazy="joined")
    cliente: Mapped[Cliente | None] = relationship(lazy="joined")
    atendida_por: Mapped[Usuario] = relationship(foreign_keys=[atendida_por_id], lazy="joined")
    autorizada_por: Mapped[Usuario | None] = relationship(foreign_keys=[autorizada_por_id], lazy="joined")
    itens: Mapped[list["ItemAcerto"]] = relationship(
        back_populates="acerto", cascade="all, delete-orphan", order_by="ItemAcerto.ordem", lazy="selectin")
    pagamentos: Mapped[list["PagamentoAcerto"]] = relationship(
        back_populates="acerto", cascade="all, delete-orphan", order_by="PagamentoAcerto.ordem", lazy="selectin")

    @property
    def negociado(self) -> Decimal:
        return self.total_inicial + self.diferenca

    @property
    def entrada(self) -> Decimal:
        """O que foi pago no caixa (no à vista, tudo)."""
        return sum((p.valor for p in self.pagamentos), Decimal("0.00"))

    @property
    def a_prazo(self) -> Decimal:
        return self.valor - self.entrada if self.pagamento == A_PRAZO else Decimal("0.00")


class ItemAcerto(Base):
    __tablename__ = "consignacao_acerto_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    acerto_id: Mapped[int] = mapped_column(ForeignKey("consignacao_acerto.id", ondelete="CASCADE"), index=True)
    ordem: Mapped[int] = mapped_column(Integer)
    # de que item de transferência a peça sai, como na devolução
    item_transferencia_id: Mapped[int] = mapped_column(ForeignKey("consignacao_transferencia_item.id"), index=True)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    preco: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # o da transferência, ou o de queima

    acerto: Mapped[Acerto] = relationship(back_populates="itens")
    item_transferencia: Mapped[ItemTransferencia] = relationship(lazy="joined")

    @property
    def total(self) -> Decimal:
        return (self.quantidade * self.preco).quantize(Decimal("0.01"))


class PagamentoAcerto(Base):
    """O que foi pago no caixa: o acerto à vista todo, ou a entrada do acerto a prazo."""

    __tablename__ = "consignacao_acerto_pagamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    acerto_id: Mapped[int] = mapped_column(ForeignKey("consignacao_acerto.id", ondelete="CASCADE"), index=True)
    ordem: Mapped[int] = mapped_column(Integer)
    forma_pagamento_id: Mapped[int] = mapped_column(ForeignKey("forma_pagamento.id"))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    parcelas: Mapped[int] = mapped_column(Integer, default=1)  # no cartão de crédito

    acerto: Mapped[Acerto] = relationship(back_populates="pagamentos")
    forma_pagamento: Mapped[FormaPagamento] = relationship(lazy="joined")


class ComissaoParcela(Base):
    """A parte da comissão do acerto para o cliente que vai em cada parcela do carnê (tab_comissparc do VB6): fica
    liberada no vencimento e vai sendo baixada conforme a loja paga ao representante.

    As linhas importadas do VB6 não têm o acerto (que não veio) e, se o carnê já estava quitado, nem a parcela: o que o
    relatório mostra delas fica nos campos *_legado."""

    __tablename__ = "consignacao_comissao_parcela"
    __table_args__ = (UniqueConstraint("empresa_id", "legado"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    acerto_id: Mapped[int | None] = mapped_column(ForeignKey("consignacao_acerto.id"), index=True)
    representante_id: Mapped[int] = mapped_column(ForeignKey("representante.id"), index=True)
    parcela_id: Mapped[int | None] = mapped_column(ForeignKey("conta_receber_parcela.id"), unique=True)
    # o vencimento com que a parcela nasceu; não acompanha a prorrogação, como no VB6
    vencimento: Mapped[date] = mapped_column(Date, index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # no VB6 há linhas negativas
    pago: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    legado: Mapped[str | None] = mapped_column(String(7))  # seq_itd
    acerto_legado: Mapped[str | None] = mapped_column(String(7))
    data_acerto_legado: Mapped[date | None] = mapped_column(Date)
    cliente_legado: Mapped[str | None] = mapped_column(String(80))
    parcela_legado: Mapped[str | None] = mapped_column(String(20))  # "2/5" ou "cheque 2/5"
    valor_parcela_legado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    @property
    def situacao(self) -> str:
        if self.pago == self.valor:
            return "paga"
        return "parcial" if self.pago else "aberta"


class PagamentoComissao(Base):
    """O que a loja pagou ao representante: sai do caixa e baixa as comissões liberadas. Os importados do VB6 não
    têm lançamento, forma nem usuário."""

    __tablename__ = "consignacao_comissao_pagamento"
    __table_args__ = (UniqueConstraint("empresa_id", "legado"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    representante_id: Mapped[int] = mapped_column(ForeignKey("representante.id"), index=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    forma_pagamento_id: Mapped[int | None] = mapped_column(ForeignKey("forma_pagamento.id"))
    lancamento_id: Mapped[int | None] = mapped_column(ForeignKey("caixa_lancamento.id"))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    estornado_em: Mapped[datetime | None] = mapped_column(DateTime)
    estornado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    legado: Mapped[str | None] = mapped_column(String(7))  # seq_cai

    representante: Mapped[Representante] = relationship(lazy="joined")
    forma_pagamento: Mapped[FormaPagamento | None] = relationship(lazy="joined")
    usuario: Mapped[Usuario | None] = relationship(foreign_keys=[usuario_id], lazy="joined")
    estornado_por: Mapped[Usuario | None] = relationship(foreign_keys=[estornado_por_id], lazy="joined")
    baixas: Mapped[list["BaixaComissao"]] = relationship(back_populates="pagamento", cascade="all, delete-orphan")


class BaixaComissao(Base):
    """Quanto de cada comissão um pagamento baixou: o pagamento parcial deixa o resto da linha em aberto."""

    __tablename__ = "consignacao_comissao_baixa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pagamento_id: Mapped[int] = mapped_column(ForeignKey("consignacao_comissao_pagamento.id", ondelete="CASCADE"), index=True)
    comissao_id: Mapped[int] = mapped_column(ForeignKey("consignacao_comissao_parcela.id"), index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    pagamento: Mapped[PagamentoComissao] = relationship(back_populates="baixas")
    comissao: Mapped[ComissaoParcela] = relationship()

