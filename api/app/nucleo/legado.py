"""De onde veio cada registro importado do VB6 (decisão D8).

O mesmo código antigo se repete entre filiais (cada banco gerava o seu com
max()+1), então a chave é a tabela de origem + a empresa + o código. É esta
tabela que torna o ETL repetível e liga dados antigos aos registros novos.
"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.banco import Base, ComDatas


class MapaLegado(ComDatas, Base):
    __tablename__ = "legado_mapa"

    tabela: Mapped[str] = mapped_column(String(40), primary_key=True)  # tabela no VB6, ex.: tab_funcionarios
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), primary_key=True)  # chave antiga, ex.: cod_fun
    novo_id: Mapped[int] = mapped_column(Integer)
