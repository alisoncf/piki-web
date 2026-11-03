"""Formas de pagamento e caixa da loja (D26). No VB6: tab_formaspag, tab_caixas e tab_caixa.

O caixa é o ponto de recebimento (Cx 02, Crediário...), não a pessoa: várias
pessoas lançam no mesmo caixa, e cada lançamento guarda quem fez. O caixa é
aberto com o fundo de troco e fechado com a conferência do que foi contado.
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Usuario
from app.dominios.financeiro.modelos import ContaPlano
from app.dominios.funcionarios.modelos import Funcionario
from app.nucleo.banco import Base, ComDatas

# tipo da forma: diz como o sistema trata o pagamento; o código é o tPag da NFC-e
TIPOS_DE_FORMA = {
    "dinheiro": ("Dinheiro", "01"),
    "pix": ("PIX", "17"),
    "cartao_credito": ("Cartão de crédito", "03"),
    "cartao_debito": ("Cartão de débito", "04"),
    "crediario": ("Crediário da loja", "05"),
    "cartao_presente": ("Cartão presente", "99"),
    "deposito": ("Depósito bancário", "16"),
    "vale": ("Vale", "99"),
    "outro": ("Outro", "99"),
}

# motivo dos lançamentos avulsos, feitos na tela do caixa
MOTIVOS = {
    "suprimento": ("entrada", "Entrada de troco"),
    "outra_entrada": ("entrada", "Outra entrada"),
    "sangria": ("saida", "Saída de troco ou retirada"),
    "despesa": ("saida", "Despesa"),
    "vale": ("saida", "Vale de funcionário"),
    "comissao": ("saida", "Comissão de cobrador"),
}

# lançados por outras telas (a venda...), e só desfeitos por lá
MOTIVOS_AUTOMATICOS = {
    "venda": ("entrada", "Venda"),
    "crediario": ("entrada", "Recebimento de crediário"),
    "cancelamento_venda": ("saida", "Cancelamento de venda"),
}

ABERTO = "aberto"
FECHADO = "fechado"


class FormaPagamento(ComDatas, Base):
    """Dinheiro, PIX, cartão, crediário... Uma lista só para todas as lojas."""

    __tablename__ = "forma_pagamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(30), unique=True)
    tipo: Mapped[str] = mapped_column(String(20))  # ver TIPOS_DE_FORMA
    desconto: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # % de desconto na venda com esta forma
    parcelas: Mapped[int] = mapped_column(Integer, default=1)  # máximo de parcelas
    # acima disto, as parcelas pedem autorização da gerência
    parcelas_sem_autorizacao: Mapped[int] = mapped_column(Integer, default=1)
    intervalo: Mapped[int] = mapped_column(Integer, default=30)  # dias entre as parcelas
    # crediário: % ao mês sugerido de juros na parcela atrasada, por dia de atraso (juros_par do VB6)
    juros_atraso: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default="0", default=Decimal(0))
    ordem: Mapped[int] = mapped_column(Integer, default=0)  # na tela da venda
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def codigo_nfce(self) -> str:
        return TIPOS_DE_FORMA.get(self.tipo, ("", "99"))[1]


class Caixa(ComDatas, Base):
    """Um ponto de recebimento da loja."""

    __tablename__ = "caixa"
    __table_args__ = (UniqueConstraint("empresa_id", "nome"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    nome: Mapped[str] = mapped_column(String(30))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class SessaoCaixa(Base):
    """Do abrir ao fechar do caixa."""

    __tablename__ = "caixa_sessao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    caixa_id: Mapped[int] = mapped_column(ForeignKey("caixa.id"), index=True)
    situacao: Mapped[str] = mapped_column(String(10), default=ABERTO)
    fundo: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)  # troco com que abriu, em dinheiro
    aberto_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    aberto_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    fechado_em: Mapped[datetime | None] = mapped_column(DateTime)
    fechado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    observacao: Mapped[str | None] = mapped_column(Text)  # do fechamento

    caixa: Mapped[Caixa] = relationship(lazy="joined")
    aberto_por: Mapped[Usuario] = relationship(foreign_keys=[aberto_por_id], lazy="joined")
    fechado_por: Mapped[Usuario | None] = relationship(foreign_keys=[fechado_por_id], lazy="joined")
    lancamentos: Mapped[list["LancamentoCaixa"]] = relationship(
        back_populates="sessao", order_by="LancamentoCaixa.id", lazy="selectin"
    )
    conferencia: Mapped[list["ConferenciaCaixa"]] = relationship(
        back_populates="sessao", cascade="all, delete-orphan", order_by="ConferenciaCaixa.id", lazy="selectin"
    )


class LancamentoCaixa(Base):
    """Uma entrada ou saída de dinheiro (ou de outra forma) no caixa."""

    __tablename__ = "caixa_lancamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sessao_id: Mapped[int] = mapped_column(ForeignKey("caixa_sessao.id"), index=True)
    data_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    tipo: Mapped[str] = mapped_column(String(7))  # entrada ou saida
    motivo: Mapped[str] = mapped_column(String(20))  # ver MOTIVOS
    forma_pagamento_id: Mapped[int] = mapped_column(ForeignKey("forma_pagamento.id"))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))  # sempre positivo; o tipo diz se entra ou sai
    historico: Mapped[str | None] = mapped_column(String(80))
    funcionario_id: Mapped[int | None] = mapped_column(ForeignKey("funcionario.id"))  # do vale ou da comissão
    # na despesa e na outra entrada: para onde foi (ou de onde veio) o dinheiro, no plano de contas
    plano_conta_id: Mapped[int | None] = mapped_column(ForeignKey("plano_conta.id"))
    documento: Mapped[str | None] = mapped_column(String(40))  # "venda 123"
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    # o lançamento errado não some: é estornado, com quem e quando
    estornado_em: Mapped[datetime | None] = mapped_column(DateTime)
    estornado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))

    sessao: Mapped[SessaoCaixa] = relationship(back_populates="lancamentos")
    forma_pagamento: Mapped[FormaPagamento] = relationship(lazy="joined")
    funcionario: Mapped[Funcionario | None] = relationship(lazy="joined")
    plano_conta: Mapped[ContaPlano | None] = relationship(lazy="joined")
    usuario: Mapped[Usuario] = relationship(foreign_keys=[usuario_id], lazy="joined")
    estornado_por: Mapped[Usuario | None] = relationship(foreign_keys=[estornado_por_id], lazy="joined")

    @property
    def descricao_motivo(self) -> str:
        return (MOTIVOS | MOTIVOS_AUTOMATICOS).get(self.motivo, ("", self.motivo))[1]


class ConferenciaCaixa(Base):
    """No fechamento: o que o sistema esperava e o que foi contado, por forma de pagamento."""

    __tablename__ = "caixa_conferencia"
    __table_args__ = (UniqueConstraint("sessao_id", "forma_pagamento_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sessao_id: Mapped[int] = mapped_column(ForeignKey("caixa_sessao.id", ondelete="CASCADE"), index=True)
    forma_pagamento_id: Mapped[int] = mapped_column(ForeignKey("forma_pagamento.id"))
    esperado: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    contado: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    sessao: Mapped[SessaoCaixa] = relationship(back_populates="conferencia")
    forma_pagamento: Mapped[FormaPagamento] = relationship(lazy="joined")

    @property
    def diferenca(self) -> Decimal:
        return self.contado - self.esperado
