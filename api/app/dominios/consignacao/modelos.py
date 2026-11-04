"""Consignação (D30): os representantes, que levam mercadoria da loja e acertam o que venderam.

O representante é um cliente especializado (Alison, 03/11/2026): os dados pessoais, o
endereço e os telefones são os da ficha do cliente; aqui ficam só os do consignado
(limite, situação, senha, comissões, avalista). Cadastro global, como o cliente; hoje só a
matriz trabalha com consignado. No VB6: tab_representantes, tab_reptip.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.clientes.modelos import Cliente
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
