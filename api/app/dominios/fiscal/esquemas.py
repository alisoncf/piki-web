from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class UsuarioResumido(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class Nota(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ambiente: str
    modelo: str
    serie: int
    numero: int
    chave: str
    situacao: str
    venda_id: int | None
    emitida_em: datetime
    emitida_por: UsuarioResumido
    valor: Decimal
    codigo_retorno: str | None
    motivo_retorno: str | None
    protocolo: str | None
    autorizada_em: datetime | None
    cancelada_em: datetime | None
    cancelada_por: UsuarioResumido | None
    justificativa_cancelamento: str | None
    protocolo_cancelamento: str | None


class RetornoSefaz(BaseModel):
    codigo: str
    motivo: str


class CancelamentoDados(BaseModel):
    justificativa: str = Field(min_length=15, max_length=255)


class EmitenteDanfe(BaseModel):
    razao_social: str | None
    cnpj: str | None
    inscricao_estadual: str | None
    endereco: str


class ItemDanfe(BaseModel):
    codigo: str | None
    descricao: str | None
    quantidade: Decimal
    unidade: str | None
    preco: Decimal
    total: Decimal


class PagamentoDanfe(BaseModel):
    tipo: str | None
    descricao: str | None
    valor: Decimal


class ConsumidorDanfe(BaseModel):
    documento: str | None
    nome: str | None


class Danfe(BaseModel):
    """O DANFE NFC-e, lido do XML autorizado."""

    situacao: str
    emitente: EmitenteDanfe
    itens: list[ItemDanfe]
    produtos: Decimal
    descontos: Decimal
    outros: Decimal
    total: Decimal
    pagamentos: list[PagamentoDanfe]
    troco: Decimal | None
    consumidor: ConsumidorDanfe | None
    numero: int
    serie: int
    emissao: datetime
    ambiente: str
    chave: str
    url_consulta: str | None
    protocolo: str | None
    autorizada_em: datetime | None
    qrcode: str | None
    qrcode_svg: str | None
    informacoes: str | None
