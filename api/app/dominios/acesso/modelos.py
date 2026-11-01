"""Usuários, perfis e permissões (decisões D9 e D10). As empresas ficam no domínio empresas."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.empresas.modelos import Empresa
from app.nucleo.banco import Base, ComDatas


perfil_permissao = Table(
    "perfil_permissao",
    Base.metadata,
    Column("perfil_id", ForeignKey("perfil.id", ondelete="CASCADE"), primary_key=True),
    Column("permissao_codigo", ForeignKey("permissao.codigo", ondelete="CASCADE"), primary_key=True),
)


class Permissao(Base):
    __tablename__ = "permissao"

    codigo: Mapped[str] = mapped_column(String(50), primary_key=True)
    descricao: Mapped[str] = mapped_column(String(150))


class Perfil(ComDatas, Base):
    """Conjunto de permissões, por exemplo "Caixa" ou "Gerente"."""

    __tablename__ = "perfil"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True)
    descricao: Mapped[str | None] = mapped_column(String(150))
    permissoes: Mapped[list[Permissao]] = relationship(secondary=perfil_permissao, lazy="selectin")


class Usuario(ComDatas, Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(String(30), unique=True)
    nome: Mapped[str] = mapped_column(String(80))
    hash_senha: Mapped[str | None] = mapped_column(String(255))
    # senha importada do VB6: conferida sem diferenciar maiúsculas até ser trocada
    senha_sem_caixa: Mapped[bool] = mapped_column(Boolean, default=False)
    administrador: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime)
    ultima_empresa_id: Mapped[int | None] = mapped_column(ForeignKey("empresa.id", ondelete="SET NULL"))
    # funcionário que usa este login (opcional: nem todo funcionário tem login, nem todo login é de funcionário)
    funcionario_id: Mapped[int | None] = mapped_column(ForeignKey("funcionario.id", ondelete="SET NULL"), unique=True)

    acessos: Mapped[list["UsuarioEmpresa"]] = relationship(back_populates="usuario", lazy="selectin")


class UsuarioEmpresa(Base):
    """A que empresas o usuário tem acesso, e com qual perfil em cada uma."""

    __tablename__ = "usuario_empresa"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id", ondelete="CASCADE"), primary_key=True)
    perfil_id: Mapped[int] = mapped_column(ForeignKey("perfil.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    usuario: Mapped[Usuario] = relationship(back_populates="acessos")
    empresa: Mapped[Empresa] = relationship(lazy="joined")
    perfil: Mapped[Perfil] = relationship(lazy="joined")
