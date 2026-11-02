"""Entrada de notas pelo XML da NF-e (D25). No VB6: tab_compras e tab_itcompras.

A nota fica aberta enquanto os itens são ligados aos produtos; ao confirmar,
o estoque da loja recebe as unidades e o produto, o custo da nota.
"""
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Usuario
from app.dominios.fornecedores.modelos import Fornecedor
from app.dominios.produtos.modelos import Produto
from app.nucleo.banco import Base, ComDatas

ABERTA = "aberta"
CONFIRMADA = "confirmada"


class NotaEntrada(ComDatas, Base):
    __tablename__ = "nota_entrada"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id"), index=True)
    chave: Mapped[str] = mapped_column(String(44), unique=True)  # uma nota só entra uma vez
    numero: Mapped[int] = mapped_column(Integer)
    serie: Mapped[int] = mapped_column(Integer)
    data_emissao: Mapped[datetime] = mapped_column(DateTime)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    situacao: Mapped[str] = mapped_column(String(12), default=ABERTA)
    arquivo: Mapped[str] = mapped_column(String(200))  # chave do XML no armazenamento (app/nucleo/arquivos.py)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))  # quem carregou
    confirmada_em: Mapped[datetime | None] = mapped_column(DateTime)
    confirmada_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))

    fornecedor: Mapped[Fornecedor] = relationship(lazy="joined")
    usuario: Mapped[Usuario | None] = relationship(foreign_keys=[usuario_id], lazy="joined")
    confirmada_por: Mapped[Usuario | None] = relationship(foreign_keys=[confirmada_por_id], lazy="joined")
    itens: Mapped[list["ItemNotaEntrada"]] = relationship(
        back_populates="nota", cascade="all, delete-orphan", order_by="ItemNotaEntrada.numero", lazy="selectin"
    )


class ItemNotaEntrada(Base):
    __tablename__ = "nota_entrada_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nota_id: Mapped[int] = mapped_column(ForeignKey("nota_entrada.id", ondelete="CASCADE"), index=True)
    numero: Mapped[int] = mapped_column(Integer)
    # como veio no XML
    codigo: Mapped[str] = mapped_column(String(60))  # o código do produto para o fornecedor
    ean: Mapped[str | None] = mapped_column(String(14))
    descricao: Mapped[str] = mapped_column(String(120))
    ncm: Mapped[str | None] = mapped_column(String(8))
    cest: Mapped[str | None] = mapped_column(String(7))
    cfop: Mapped[str | None] = mapped_column(String(4))
    unidade: Mapped[str] = mapped_column(String(6))
    quantidade: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    valor_produtos: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    valor_desconto: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    valor_frete: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    valor_seguro: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    valor_outras: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    valor_ipi: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    valor_st: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    # o que a loja decide
    produto_id: Mapped[int | None] = mapped_column(ForeignKey("produto.id"), index=True)
    embalagem: Mapped[int] = mapped_column(Integer, default=1)  # unidades do produto em cada unidade da nota
    preco_venda: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))  # preço novo, se for mudar

    nota: Mapped[NotaEntrada] = relationship(back_populates="itens")
    produto: Mapped[Produto | None] = relationship(lazy="joined")

    @property
    def valor_custo(self) -> Decimal:
        """O que o item custou de verdade: produtos − desconto + frete, seguro, outras despesas, IPI e ST."""
        return (self.valor_produtos - self.valor_desconto + self.valor_frete + self.valor_seguro
                + self.valor_outras + self.valor_ipi + self.valor_st)

    @property
    def unidades(self) -> Decimal:
        """Quantas unidades do produto entram no estoque."""
        return self.quantidade * (self.embalagem or 1)

    @property
    def custo_unitario(self) -> Decimal | None:
        if not self.unidades:
            return None
        return (self.valor_custo / self.unidades).quantize(Decimal("0.01"), ROUND_HALF_UP)
