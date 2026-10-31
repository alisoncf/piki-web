"""Clientes e seus cadastros de apoio (cadastro global, D9).

No VB6: tab_clientes, tab_telefones (tipo_ter = 'C'), tab_referencias,
tab_tipopar, tab_clientesanot, tab_setores, tab_orgaos, tab_grupocli e tab_contacob. Cada loja
tinha os seus setores, órgãos e cobradores; aqui são uma lista só. Cobradores valem para
todas as lojas: um setor pode ter vários cobradores, e um cobrador, vários setores.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Table, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Empresa, Usuario
from app.dominios.cidades.modelos import Cidade
from app.nucleo.banco import Base, ComDatas


class GrupoCliente(ComDatas, Base):
    """Geral, servidor municipal, estadual, federal... (tab_grupocli)."""

    __tablename__ = "grupo_cliente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(40), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Parentesco(ComDatas, Base):
    """Relação da referência com o cliente: cônjuge, pais, amigo... (tab_tipopar)."""

    __tablename__ = "parentesco"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(30), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Cobrador(ComDatas, Base):
    """Quem cobra os setores: pessoa ou destino da cobrança (escritório, advogado...). tab_contacob no VB6."""

    __tablename__ = "cobrador"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(40), unique=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


setor_cobrador = Table(
    "setor_cobrador",
    Base.metadata,
    Column("setor_id", ForeignKey("setor.id", ondelete="CASCADE"), primary_key=True),
    Column("cobrador_id", ForeignKey("cobrador.id", ondelete="CASCADE"), primary_key=True),
)


class Setor(ComDatas, Base):
    """Bairro ou região de cobrança (tab_setores), sempre numa cidade do IBGE."""

    __tablename__ = "setor"
    __table_args__ = (UniqueConstraint("nome", "cidade_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(40))
    tipo: Mapped[str | None] = mapped_column(String(20))  # bairro, vila, setor, jardim... (tipo_set)
    cidade_id: Mapped[int | None] = mapped_column(ForeignKey("cidade.id"), index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    cidade: Mapped[Cidade | None] = relationship(lazy="joined")
    cobradores: Mapped[list[Cobrador]] = relationship(
        secondary=setor_cobrador, lazy="selectin", order_by=Cobrador.nome
    )


class Orgao(ComDatas, Base):
    """Onde o cliente trabalha: escola, prefeitura, empresa (tab_orgaos)."""

    __tablename__ = "orgao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), unique=True)
    grupo_id: Mapped[int | None] = mapped_column(ForeignKey("grupo_cliente.id"))
    setor_id: Mapped[int | None] = mapped_column(ForeignKey("setor.id"))
    endereco: Mapped[str | None] = mapped_column(String(60))
    cep: Mapped[str | None] = mapped_column(String(8))
    telefone: Mapped[str | None] = mapped_column(String(15))
    observacao: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    grupo: Mapped[GrupoCliente | None] = relationship(lazy="joined")
    setor: Mapped[Setor | None] = relationship(lazy="joined")


class Cliente(ComDatas, Base):
    __tablename__ = "cliente"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), index=True)
    tipo: Mapped[str] = mapped_column(String(1), default="F")  # F pessoa física, J jurídica
    # CPF ou CNPJ, só dígitos; é por ele que os cadastros das lojas foram juntados
    cpf_cnpj: Mapped[str | None] = mapped_column(String(14), unique=True)
    rg: Mapped[str | None] = mapped_column(String(20))
    inscricao_estadual: Mapped[str | None] = mapped_column(String(20))
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    sexo: Mapped[str | None] = mapped_column(String(1))
    pai: Mapped[str | None] = mapped_column(String(60))
    mae: Mapped[str | None] = mapped_column(String(60))
    email: Mapped[str | None] = mapped_column(String(100))

    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None] = mapped_column(String(100))
    numero: Mapped[str | None] = mapped_column(String(20))
    complemento: Mapped[str | None] = mapped_column(String(60))
    bairro: Mapped[str | None] = mapped_column(String(40))
    ponto_referencia: Mapped[str | None] = mapped_column(String(60))
    cidade: Mapped[str | None] = mapped_column(String(40))
    uf: Mapped[str | None] = mapped_column(String(2))
    codigo_municipio: Mapped[str | None] = mapped_column(String(7))  # IBGE
    setor_id: Mapped[int | None] = mapped_column(ForeignKey("setor.id"), index=True)

    grupo_id: Mapped[int | None] = mapped_column(ForeignKey("grupo_cliente.id"))
    orgao_id: Mapped[int | None] = mapped_column(ForeignKey("orgao.id"), index=True)
    local_trabalho: Mapped[str | None] = mapped_column(String(60))
    endereco_trabalho: Mapped[str | None] = mapped_column(String(60))
    telefone_trabalho: Mapped[str | None] = mapped_column(String(15))
    cep_trabalho: Mapped[str | None] = mapped_column(String(8))
    setor_trabalho_id: Mapped[int | None] = mapped_column(ForeignKey("setor.id"))

    # bloqueado não compra a prazo (status_cli 2 no VB6)
    bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)
    # onde o cobrador recebe; ver FORMAS_COBRANCA em esquemas.py
    forma_cobranca: Mapped[str] = mapped_column(String(10), default="domicilio")
    limite_credito: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    credito_suspenso: Mapped[bool] = mapped_column(Boolean, default=False)
    recebe_mensagens: Mapped[bool] = mapped_column(Boolean, default=True)
    especial: Mapped[bool] = mapped_column(Boolean, default=False)
    observacao: Mapped[str | None] = mapped_column(Text)

    data_cadastro: Mapped[date] = mapped_column(Date, default=date.today)
    # última alteração do cadastro; na importação, vence o dado da loja com a data mais recente
    data_alteracao: Mapped[date | None] = mapped_column(Date)
    empresa_cadastro_id: Mapped[int | None] = mapped_column(ForeignKey("empresa.id"))

    setor: Mapped[Setor | None] = relationship(foreign_keys=[setor_id], lazy="joined")
    setor_trabalho: Mapped[Setor | None] = relationship(foreign_keys=[setor_trabalho_id], lazy="joined")
    grupo: Mapped[GrupoCliente | None] = relationship(lazy="joined")
    orgao: Mapped[Orgao | None] = relationship(lazy="joined")
    empresa_cadastro: Mapped[Empresa | None] = relationship(lazy="joined")
    telefones: Mapped[list["TelefoneCliente"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan", order_by="TelefoneCliente.id", lazy="selectin"
    )
    referencias: Mapped[list["ReferenciaCliente"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan", order_by="ReferenciaCliente.id", lazy="selectin"
    )
    anotacoes: Mapped[list["AnotacaoCliente"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan", order_by="AnotacaoCliente.data_hora.desc()",
        lazy="selectin",
    )


class TelefoneCliente(Base):
    __tablename__ = "cliente_telefone"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id", ondelete="CASCADE"), index=True)
    numero: Mapped[str] = mapped_column(String(15), index=True)  # só dígitos, com DDD
    tipo: Mapped[str] = mapped_column(String(1))  # ver TIPOS_TELEFONE em app/nucleo/documentos.py

    cliente: Mapped[Cliente] = relationship(back_populates="telefones")


class ReferenciaCliente(Base):
    """Pessoa ou comércio que dá referência do cliente (tab_referencias)."""

    __tablename__ = "cliente_referencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id", ondelete="CASCADE"), index=True)
    nome: Mapped[str] = mapped_column(String(60))
    telefone: Mapped[str | None] = mapped_column(String(20))
    parentesco_id: Mapped[int | None] = mapped_column(ForeignKey("parentesco.id"))

    cliente: Mapped[Cliente] = relationship(back_populates="referencias")
    parentesco: Mapped[Parentesco | None] = relationship(lazy="joined")


class AnotacaoCliente(Base):
    """Anotações feitas pelas lojas sobre o cliente (tab_clientesanot). Não se alteram, só se acrescentam."""

    __tablename__ = "cliente_anotacao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id", ondelete="CASCADE"), index=True)
    texto: Mapped[str] = mapped_column(Text)
    data_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    empresa_id: Mapped[int | None] = mapped_column(ForeignKey("empresa.id"))

    cliente: Mapped[Cliente] = relationship(back_populates="anotacoes")
    empresa: Mapped[Empresa | None] = relationship(lazy="joined")
    usuario: Mapped[Usuario | None] = relationship(lazy="joined")
