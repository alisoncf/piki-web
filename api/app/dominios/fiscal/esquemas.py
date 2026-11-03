from datetime import datetime
from decimal import Decimal
from typing import Literal

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
    destinatario: str | None
    codigo_retorno: str | None
    motivo_retorno: str | None
    protocolo: str | None
    autorizada_em: datetime | None
    cancelada_em: datetime | None
    cancelada_por: UsuarioResumido | None
    justificativa_cancelamento: str | None
    protocolo_cancelamento: str | None


class Serie(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    modelo: str
    serie: int
    ultimo: int


class Faixa(BaseModel):
    inicial: int
    final: int


class Lacunas(BaseModel):
    faixas: list[Faixa]
    pendentes: list[int] = Field(description="Notas sem resposta da SEFAZ no meio da série: consultar antes")


class InutilizacaoDados(BaseModel):
    modelo: Literal["65", "55"] = "65"
    serie: int = Field(ge=0, le=999)
    inicial: int = Field(ge=1, le=999999999)
    final: int = Field(ge=1, le=999999999)
    justificativa: str = Field(min_length=15, max_length=255)


class Inutilizacao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ambiente: str
    modelo: str
    serie: int
    inicial: int
    final: int
    justificativa: str
    protocolo: str | None
    homologada_em: datetime | None
    feita_por: UsuarioResumido


class OperacaoDados(BaseModel):
    natureza: str = Field(min_length=1, max_length=60)
    tipo: Literal["0", "1"] = Field(description="0 entrada, 1 saída")
    finalidade: Literal["1", "2", "3", "4"] = Field(description="1 normal, 2 complementar, 3 ajuste, 4 devolução")
    cfop_estado: str = Field(pattern=r"^\d{4}$")
    cfop_fora: str = Field(pattern=r"^\d{4}$")


class Operacao(OperacaoDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uso: str


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
