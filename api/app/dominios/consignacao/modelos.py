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

