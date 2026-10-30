"""Clientes e seus cadastros de apoio (cadastro global, D9).

No VB6: tab_clientes, tab_telefones (tipo_ter = 'C'), tab_referencias,
tab_tipopar, tab_clientesanot, tab_setores, tab_orgaos e tab_grupocli. Cada loja tinha os
seus setores e órgãos; aqui são uma lista só. O cobrador de cada setor é
escolhido por loja (setor_cobrador).
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.modelos import Empresa, Usuario
from app.dominios.funcionarios.modelos import Funcionario
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


class Setor(ComDatas, Base):
    """Bairro ou região de cobrança (tab_setores). Os clientes de um setor são visitados pelo mesmo cobrador."""

    __tablename__ = "setor"
    __table_args__ = (UniqueConstraint("nome", "cidade"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(40))
    tipo: Mapped[str | None] = mapped_column(String(20))  # bairro, vila, setor, jardim... (tipo_set)
    cidade: Mapped[str | None] = mapped_column(String(40))
    uf: Mapped[str | None] = mapped_column(String(2))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    cobradores: Mapped[list["SetorCobrador"]] = relationship(
        back_populates="setor", cascade="all, delete-orphan", lazy="selectin"
    )


class SetorCobrador(ComDatas, Base):
    """Quem cobra o setor em cada loja (cobrador_set no VB6, que era de cada banco)."""

    __tablename__ = "setor_cobrador"

    setor_id: Mapped[int] = mapped_column(ForeignKey("setor.id", ondelete="CASCADE"), primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), primary_key=True)
    funcionario_id: Mapped[int] = mapped_column(ForeignKey("funcionario.id"))

    setor: Mapped[Setor] = relationship(back_populates="cobradores")
    empresa: Mapped[Empresa] = relationship(lazy="joined")
    funcionario: Mapped[Funcionario] = relationship(lazy="joined")


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
