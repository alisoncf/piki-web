"""Fornecedores (cadastro global, D9; D22). No VB6: tab_fornecedores e tab_telefones com tipo_ter 'F'."""
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.cidades.modelos import Cidade
from app.nucleo.banco import Base, ComDatas


class Fornecedor(ComDatas, Base):
    """Quem vende para a loja: indústria, distribuidor, transportadora, prestador. Sempre com CPF ou CNPJ válido."""

    __tablename__ = "fornecedor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # razão social (ou o nome, se for pessoa física)
    nome: Mapped[str] = mapped_column(String(100))
    nome_fantasia: Mapped[str | None] = mapped_column(String(60))
    cpf_cnpj: Mapped[str] = mapped_column(String(14), unique=True)  # só dígitos; 11 = pessoa física
    inscricao_estadual: Mapped[str | None] = mapped_column(String(20))

    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None] = mapped_column(String(60))
    numero: Mapped[str | None] = mapped_column(String(10))
    complemento: Mapped[str | None] = mapped_column(String(60))
    # texto, como na empresa: o setor é região de cobrança de clientes
    bairro: Mapped[str | None] = mapped_column(String(60))
    cidade_id: Mapped[int | None] = mapped_column(ForeignKey("cidade.id"), index=True)

    email: Mapped[str | None] = mapped_column(String(200))
    site: Mapped[str | None] = mapped_column(String(200))
    observacao: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    cidade: Mapped[Cidade | None] = relationship(lazy="joined")
    telefones: Mapped[list["TelefoneFornecedor"]] = relationship(
        back_populates="fornecedor", cascade="all, delete-orphan", order_by="TelefoneFornecedor.id", lazy="selectin"
    )
    contatos: Mapped[list["ContatoFornecedor"]] = relationship(
        back_populates="fornecedor", cascade="all, delete-orphan", order_by="ContatoFornecedor.id", lazy="selectin"
    )

    @property
    def tipo(self) -> str:
        return "F" if len(self.cpf_cnpj) == 11 else "J"


class TelefoneFornecedor(Base):
    """Telefones da empresa do fornecedor (os das pessoas ficam nos contatos)."""

    __tablename__ = "fornecedor_telefone"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id", ondelete="CASCADE"), index=True)
    numero: Mapped[str] = mapped_column(String(15))  # só dígitos, com DDD
    tipo: Mapped[str] = mapped_column(String(1))  # ver TIPOS_TELEFONE em app/nucleo/documentos.py

    fornecedor: Mapped[Fornecedor] = relationship(back_populates="telefones")


class ContatoFornecedor(Base):
    """Uma pessoa do fornecedor: o representante, o financeiro, o vendedor interno..."""

    __tablename__ = "fornecedor_contato"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedor.id", ondelete="CASCADE"), index=True)
    nome: Mapped[str] = mapped_column(String(60))
    funcao: Mapped[str | None] = mapped_column(String(40))
    telefone: Mapped[str | None] = mapped_column(String(15))  # só dígitos, com DDD
    email: Mapped[str | None] = mapped_column(String(200))

    fornecedor: Mapped[Fornecedor] = relationship(back_populates="contatos")
