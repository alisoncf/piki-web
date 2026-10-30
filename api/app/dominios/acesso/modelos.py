"""Empresas, usuários, perfis e permissões (decisões D9 e D10)."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dominios.acesso.cores import cor_hex
from app.nucleo.banco import Base, ComDatas


class Empresa(ComDatas, Base):
    """Uma filial, com CNPJ próprio."""

    __tablename__ = "empresa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # código usado no VB6 (cod_emp / sped_empresa.codigo); o ETL usa para saber de onde veio cada dado
    codigo: Mapped[str] = mapped_column(String(2), unique=True)
    # nome curto, mostrado na escolha e na troca de empresa (no VB6: apelido)
    nome: Mapped[str] = mapped_column(String(60))
    razao_social: Mapped[str | None] = mapped_column(String(100))
    nome_fantasia: Mapped[str | None] = mapped_column(String(60))
    cnpj: Mapped[str | None] = mapped_column(String(14), unique=True)
    inscricao_estadual: Mapped[str | None] = mapped_column(String(20))
    inscricao_municipal: Mapped[str | None] = mapped_column(String(20))
    # código de regime tributário da NF-e: 1 Simples Nacional, 2 Simples com excesso, 3 Regime normal
    crt: Mapped[str | None] = mapped_column(String(1))
    # perfil (A, B, C) e tipo de atividade (0 industrial, 1 outros) do SPED Fiscal
    sped_perfil: Mapped[str | None] = mapped_column(String(1))
    sped_atividade: Mapped[str | None] = mapped_column(String(1))

    uf: Mapped[str | None] = mapped_column(String(2))
    codigo_municipio: Mapped[str | None] = mapped_column(String(7))  # IBGE
    cep: Mapped[str | None] = mapped_column(String(8))
    logradouro: Mapped[str | None] = mapped_column(String(60))
    numero: Mapped[str | None] = mapped_column(String(10))
    complemento: Mapped[str | None] = mapped_column(String(60))
    bairro: Mapped[str | None] = mapped_column(String(60))
    telefone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(200))

    ativa: Mapped[bool] = mapped_column(Boolean, server_default=true(), default=True)
    # cor de identificação na tela, um nome da paleta de cores.py; vazia = automática pelo código
    cor: Mapped[str | None] = mapped_column(String(20))

    @property
    def cor_hex(self) -> str:
        return cor_hex(self.cor, self.codigo)


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
