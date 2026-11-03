"""Notas fiscais (D29): NFC-e (modelo 65) e NF-e (modelo 55), emitidas pela própria API.

A numeração guarda o último número usado em cada modelo e série da loja, em cada ambiente
(os testes em homologação não gastam os números de produção). A série é a do caixa (101 é o
caixa 01, como no VB6). Na virada da loja, a numeração de produção continua de onde o VB6
parou (python -m etl notas).
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from app.dominios.acesso.modelos import Usuario
from app.nucleo.banco import Base, ComDatas

MODELOS = {"65": "NFC-e", "55": "NF-e"}
AMBIENTES = {"1": "Produção", "2": "Homologação"}

# situação da nota: pendente (enviada sem resposta, ou a resposta se perdeu: consultar ou retransmitir),
# rejeitada (a SEFAZ recusou: corrigir e transmitir de novo, com o mesmo número), autorizada,
# cancelada, denegada, inutilizada (a rejeitada cujo número foi inutilizado; a venda, se precisar, ganha outro)
PENDENTE = "pendente"
REJEITADA = "rejeitada"
AUTORIZADA = "autorizada"
CANCELADA = "cancelada"
DENEGADA = "denegada"
INUTILIZADA = "inutilizada"
SITUACOES = (PENDENTE, REJEITADA, AUTORIZADA, CANCELADA, DENEGADA, INUTILIZADA)


class NumeracaoNota(ComDatas, Base):
    __tablename__ = "nota_numeracao"
    __table_args__ = (UniqueConstraint("empresa_id", "ambiente", "modelo", "serie"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    ambiente: Mapped[str] = mapped_column(String(1), server_default="1", default="1")  # ver AMBIENTES
    modelo: Mapped[str] = mapped_column(String(2))  # ver MODELOS
    serie: Mapped[int] = mapped_column(Integer)
    ultimo: Mapped[int] = mapped_column(Integer, default=0)  # o último número usado


class NotaFiscal(ComDatas, Base):
    """Uma nota emitida pela loja. O XML guardado é o assinado (ou, autorizada, o nfeProc, com o protocolo)."""

    __tablename__ = "nota_fiscal"
    __table_args__ = (UniqueConstraint("empresa_id", "ambiente", "modelo", "serie", "numero"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    ambiente: Mapped[str] = mapped_column(String(1))
    modelo: Mapped[str] = mapped_column(String(2))
    serie: Mapped[int] = mapped_column(Integer)
    numero: Mapped[int] = mapped_column(Integer)
    codigo_numerico: Mapped[str] = mapped_column(String(8))  # o cNF, que entra na chave
    chave: Mapped[str] = mapped_column(String(44), index=True)
    situacao: Mapped[str] = mapped_column(String(12), default=PENDENTE, index=True)
    venda_id: Mapped[int | None] = mapped_column(ForeignKey("venda.id"), index=True)
    emitida_em: Mapped[datetime] = mapped_column(DateTime)
    emitida_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    # a última resposta da SEFAZ (cStat e xMotivo)
    codigo_retorno: Mapped[str | None] = mapped_column(String(3))
    motivo_retorno: Mapped[str | None] = mapped_column(String(255))
    protocolo: Mapped[str | None] = mapped_column(String(15))
    autorizada_em: Mapped[datetime | None] = mapped_column(DateTime)
    xml: Mapped[str] = deferred(mapped_column(Text))

    cancelada_em: Mapped[datetime | None] = mapped_column(DateTime)
    cancelada_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    justificativa_cancelamento: Mapped[str | None] = mapped_column(String(255))
    protocolo_cancelamento: Mapped[str | None] = mapped_column(String(15))
    xml_cancelamento: Mapped[str | None] = deferred(mapped_column(Text))  # o retEvento, com o protocolo do cancelamento

    emitida_por: Mapped[Usuario] = relationship(foreign_keys=[emitida_por_id], lazy="joined")
    cancelada_por: Mapped[Usuario | None] = relationship(foreign_keys=[cancelada_por_id], lazy="joined")


class InutilizacaoNota(ComDatas, Base):
    """Uma faixa de números que não vai ser usada (as lacunas da série), homologada pela SEFAZ."""

    __tablename__ = "nota_inutilizacao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"), index=True)
    ambiente: Mapped[str] = mapped_column(String(1))
    modelo: Mapped[str] = mapped_column(String(2))
    serie: Mapped[int] = mapped_column(Integer)
    inicial: Mapped[int] = mapped_column(Integer)
    final: Mapped[int] = mapped_column(Integer)
    justificativa: Mapped[str] = mapped_column(String(255))
    protocolo: Mapped[str | None] = mapped_column(String(15))
    homologada_em: Mapped[datetime | None] = mapped_column(DateTime)
    feita_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    xml: Mapped[str | None] = deferred(mapped_column(Text))  # o retInutNFe

    feita_por: Mapped[Usuario] = relationship(lazy="joined")
