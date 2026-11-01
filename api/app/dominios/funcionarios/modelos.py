"""Funcionários e cargos (cadastro global, D9). No VB6: tab_funcionarios, tab_cargos e tab_telefones."""
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.empresas.modelos import Empresa
from app.nucleo.banco import Base, ComDatas

if TYPE_CHECKING:  # clientes importa funcionários (cobradores do setor)
    from app.dominios.clientes.modelos import Setor


class Cargo(ComDatas, Base):
    __tablename__ = "cargo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(40), unique=True)
    # quem tem o cargo aparece na escolha de vendedor da venda (venda_car no VB6)
    vende: Mapped[bool] = mapped_column(Boolean, default=False)
    # quem tem o cargo aparece na escolha de cobrador (cobranca_car no VB6)
    cobra: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Funcionario(ComDatas, Base):
    __tablename__ = "funcionario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    # como é chamado na loja (guerra_fun no VB6, que também era o login)
    apelido: Mapped[str | None] = mapped_column(String(30))
    cpf: Mapped[str | None] = mapped_column(String(11), unique=True)
    rg: Mapped[str | None] = mapped_column(String(20))
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    sexo: Mapped[str | None] = mapped_column(String(1))  # M ou F
    naturalidade: Mapped[str | None] = mapped_column(String(40))

    # loja onde trabalha; muda se for transferido
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    cargo_id: Mapped[int | None] = mapped_column(ForeignKey("cargo.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    pode_tirar_vale: Mapped[bool] = mapped_column(Boolean, default=True)
    # limite para vales e compras do próprio funcionário (limite_fun no VB6)
    limite_vale: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))

    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None] = mapped_column(String(60))
    # bairro e cidade vêm do setor (D17)
    setor_id: Mapped[int | None] = mapped_column(ForeignKey("setor.id"), index=True)

    conjuge: Mapped[str | None] = mapped_column(String(60))
    pai: Mapped[str | None] = mapped_column(String(60))
    mae: Mapped[str | None] = mapped_column(String(60))
    endereco_pais: Mapped[str | None] = mapped_column(String(100))
    observacao: Mapped[str | None] = mapped_column(Text)

    empresa: Mapped[Empresa] = relationship(lazy="joined")
    cargo: Mapped[Cargo | None] = relationship(lazy="joined")
    # carregado só quando pedido: o setor traz os seus cobradores, que são funcionários
    setor: Mapped["Setor | None"] = relationship(lazy="select")
    telefones: Mapped[list["TelefoneFuncionario"]] = relationship(
        back_populates="funcionario", cascade="all, delete-orphan", order_by="TelefoneFuncionario.id", lazy="selectin"
    )


class TelefoneFuncionario(Base):
    __tablename__ = "funcionario_telefone"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    funcionario_id: Mapped[int] = mapped_column(ForeignKey("funcionario.id", ondelete="CASCADE"), index=True)
    numero: Mapped[str] = mapped_column(String(15))  # só dígitos, com DDD
    tipo: Mapped[str] = mapped_column(String(1))  # ver TIPOS_TELEFONE em app/nucleo/documentos.py

    funcionario: Mapped[Funcionario] = relationship(back_populates="telefones")
