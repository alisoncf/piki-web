"""Municípios do IBGE (cadastro global). Setores, e depois clientes e órgãos, apontam para cá.

A lista vem pronta na migração 0008 (alembic/referencia/municipios_ibge.csv, baixada da
API de localidades do IBGE). No VB6 havia a tabela `cidades` (IBGE) e a tab_cidades,
digitada em cada loja, com o código do IBGE em cod_mun.
"""
import unicodedata

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base, ComDatas


def nome_de_busca(nome: str | None) -> str:
    """Minúsculas, sem acentos e sem espaços repetidos: 'Anápolis' → 'anapolis'."""
    sem_acento = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


class Cidade(ComDatas, Base):
    __tablename__ = "cidade"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo_ibge: Mapped[str] = mapped_column(String(7), unique=True)
    nome: Mapped[str] = mapped_column(String(60))
    uf: Mapped[str] = mapped_column(String(2))
    # o nome sem acentos, para a busca funcionar igual no PostgreSQL e no SQLite
    nome_busca: Mapped[str] = mapped_column(String(60), index=True)
