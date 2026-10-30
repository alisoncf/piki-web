"""Modelos do banco.

Há dois grupos, com metadados separados:

- LegadoBase: tabelas que já existem e pertencem ao VB6. Mapeamos só as
  colunas que a API usa, com os nomes exatos do banco. A API nunca cria nem
  altera a estrutura dessas tabelas.
- WebBase: tabelas novas, criadas pelo sistema novo. A estrutura delas é
  criada pelos scripts em api/migracoes/.
"""
from datetime import datetime

from sqlalchemy import CHAR, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class LegadoBase(DeclarativeBase):
    pass


class WebBase(DeclarativeBase):
    pass


# ---------------------------------------------------------------- legado


class Usuario(LegadoBase):
    __tablename__ = "tab_usuarios"

    cod_fun: Mapped[str] = mapped_column("COD_FUN", CHAR(3), primary_key=True)
    senha: Mapped[str | None] = mapped_column("SENHA_USU", CHAR(10))
    status: Mapped[str | None] = mapped_column("Status_USU", CHAR(1))
    nivel: Mapped[str | None] = mapped_column("NIVEL_USU", CHAR(1))


class Funcionario(LegadoBase):
    __tablename__ = "tab_funcionarios"

    cod_fun: Mapped[str] = mapped_column(CHAR(3), primary_key=True)
    nome: Mapped[str | None] = mapped_column("nome_fun", CHAR(50))
    apelido: Mapped[str | None] = mapped_column("guerra_fun", CHAR(20))
    cod_cargo: Mapped[str] = mapped_column("cod_Car", CHAR(3))
    status: Mapped[str] = mapped_column("status_fun", CHAR(1))


# ------------------------------------------------------------------- web


class Credencial(WebBase):
    """Senha do usuário no sistema novo, guardada como hash (decisão D7)."""

    __tablename__ = "web_credencial"

    cod_fun: Mapped[str] = mapped_column(CHAR(3), primary_key=True)
    hash_senha: Mapped[str] = mapped_column(String(255))
    # impressão digital (sha256) do SENHA_USU do legado no momento em que o
    # hash foi gerado; se a senha mudar no VB6, o hash é refeito
    marca_legado: Mapped[str] = mapped_column(CHAR(64))
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime)
