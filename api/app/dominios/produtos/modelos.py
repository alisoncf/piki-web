"""Produtos (cadastro global, mantido pela matriz; D24). No VB6: tab_produtos, tab_secoes, tab_subsec e tab_codbarras.

Preço e custo são do produto, iguais em todas as lojas. O estoque e os
impostos que dependem do regime de cada empresa ficam por empresa, em outra
tabela (próximo passo).
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.fornecedores.modelos import Fornecedor
from app.nucleo.banco import Base, ComDatas


class Secao(ComDatas, Base):
    """Cama, mesa, banho, decoração..."""

    __tablename__ = "secao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(40), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    subsecoes: Mapped[list["Subsecao"]] = relationship(
        back_populates="secao", order_by="Subsecao.nome", lazy="selectin"
    )


class Subsecao(ComDatas, Base):
    """Jogo de cama, cobre-leito, toalha de mesa... Todo produto está numa subseção."""

    __tablename__ = "subsecao"
    __table_args__ = (UniqueConstraint("secao_id", "nome"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    secao_id: Mapped[int] = mapped_column(ForeignKey("secao.id"), index=True)
    nome: Mapped[str] = mapped_column(String(50))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    secao: Mapped[Secao] = relationship(back_populates="subsecoes", lazy="joined")


class Marca(ComDatas, Base):
    """Quem fabrica (Karsten, Döhler...). Diferente do fornecedor, de quem a loja compra."""

    __tablename__ = "marca"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Produto(ComDatas, Base):
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # o cod_pro do VB6; é também o código de barras interno, impresso com 8 dígitos (00012345)
    codigo: Mapped[int] = mapped_column(Integer, unique=True)
    # o nome completo, com tamanho, medidas e marca: cada produto é um item diferente (sem grade)
    nome: Mapped[str] = mapped_column(String(120))
    subsecao_id: Mapped[int | None] = mapped_column(ForeignKey("subsecao.id"), index=True)
    marca_id: Mapped[int | None] = mapped_column(ForeignKey("marca.id"), index=True)
    unidade: Mapped[str] = mapped_column(String(6), default="UN")
    # aceita quantidade com fração na venda (passadeira vendida por m²)
    fracionado: Mapped[bool] = mapped_column(Boolean, default=False)

    # custo da última entrada; a margem (%) é a usada para sugerir o preço na entrada
    custo: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    margem: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=0)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    # preço de queima (liquidação); vazio quando o produto não está em queima
    preco_queima: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    # dados fiscais que não dependem da empresa (os que dependem ficam no estoque de cada uma)
    ncm: Mapped[str | None] = mapped_column(String(8))
    cest: Mapped[str | None] = mapped_column(String(7))
    origem: Mapped[int] = mapped_column(SmallInteger, default=0)  # 0 nacional ... 8 (tabela da NF-e)

    observacao: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    subsecao: Mapped[Subsecao | None] = relationship(lazy="joined")
    marca: Mapped[Marca | None] = relationship(lazy="joined")
    codigos_barras: Mapped[list["CodigoBarras"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan", order_by="CodigoBarras.id", lazy="selectin"
    )
    fornecedores: Mapped[list["ProdutoFornecedor"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan", order_by="ProdutoFornecedor.id", lazy="selectin"
    )
    fotos: Mapped[list["FotoProduto"]] = relationship(
        back_populates="produto", cascade="all, delete-orphan", order_by=lambda: [FotoProduto.ordem, FotoProduto.id],
        lazy="selectin",
    )

    @property
    def fornecedor(self) -> str | None:
        """O primeiro fornecedor, pelo nome fantasia (ou a razão social), para as listas."""
        if not self.fornecedores:
            return None
        f = self.fornecedores[0].fornecedor
        return f.nome_fantasia or f.nome

    @property
    def foto_id(self) -> int | None:
        return self.fotos[0].id if self.fotos else None


class CodigoBarras(Base):
    """Códigos de barras de fábrica (EAN...). O código interno é o próprio código do produto e não entra aqui."""

    __tablename__ = "produto_codigo_barras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id", ondelete="CASCADE"), index=True)
    codigo: Mapped[str] = mapped_column(String(14), unique=True)  # só dígitos, de 8 a 14

    produto: Mapped[Produto] = relationship(back_populates="codigos_barras")


class ProdutoFornecedor(Base):
    """De quem a loja compra o produto, e o código que o fornecedor usa (liga o item da nota ao produto)."""

    __tablename__ = "produto_fornecedor"
    __table_args__ = (UniqueConstraint("produto_id", "fornecedor_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id", ondelete="CASCADE"), index=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id"), index=True)
    codigo: Mapped[str | None] = mapped_column(String(60))

    produto: Mapped[Produto] = relationship(back_populates="fornecedores")
    fornecedor: Mapped[Fornecedor] = relationship(lazy="joined")


class FotoProduto(Base):
    """Foto do produto. O arquivo fica fora do banco (app/nucleo/arquivos.py); a de menor ordem é a principal."""

    __tablename__ = "produto_foto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id", ondelete="CASCADE"), index=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    chave: Mapped[str] = mapped_column(String(200))
    tipo_conteudo: Mapped[str] = mapped_column(String(40))
    tamanho: Mapped[int] = mapped_column(Integer)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    produto: Mapped[Produto] = relationship(back_populates="fotos")
