from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.dominios.caixa.modelos import MOTIVOS, TIPOS_DE_FORMA

TipoForma = Literal[tuple(TIPOS_DE_FORMA)]  # type: ignore[valid-type]
Motivo = Literal[tuple(MOTIVOS)]  # type: ignore[valid-type]


def _vazio_para_none(valor: object) -> object:
    if isinstance(valor, str):
        return valor.strip() or None
    return valor


class FormaDados(BaseModel):
    nome: str = Field(min_length=1, max_length=30)
    tipo: TipoForma
    desconto: Decimal = Field(default=Decimal(0), ge=0, lt=100, max_digits=5, decimal_places=2, description="% na venda")
    parcelas: int = Field(default=1, ge=1, le=24, description="Máximo de parcelas")
    parcelas_sem_autorizacao: int = Field(default=1, ge=1, le=24, description="Acima disto, pede a gerência")
    intervalo: int = Field(default=30, ge=0, le=365, description="Dias entre as parcelas")
    juros_atraso: Decimal = Field(default=Decimal(0), ge=0, lt=100, max_digits=5, decimal_places=2,
                                  description="Crediário: % ao mês sugerido na parcela atrasada, por dia de atraso")
    ordem: int = 0
    ativo: bool = True

    @field_validator("nome", mode="before")
    @classmethod
    def _nome(cls, v: object) -> object:
        return _vazio_para_none(v)

    @model_validator(mode="after")
    def _parcelas(self) -> "FormaDados":
        if self.parcelas_sem_autorizacao > self.parcelas:
            self.parcelas_sem_autorizacao = self.parcelas
        return self


class Forma(FormaDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_nfce: str


class TipoDeForma(BaseModel):
    codigo: str
    nome: str


class CaixaDados(BaseModel):
    nome: str = Field(min_length=1, max_length=30)
    ativo: bool = True

    @field_validator("nome", mode="before")
    @classmethod
    def _nome(cls, v: object) -> object:
        return _vazio_para_none(v)


class Pessoa(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class SessaoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    situacao: str
    fundo: Decimal
    aberto_em: datetime
    aberto_por: Pessoa
    fechado_em: datetime | None
    fechado_por: Pessoa | None


class Caixa(CaixaDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sessao: SessaoResumo | None = Field(default=None, description="A sessão aberta, se o caixa está aberto")


class FormaResumida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo: str


class Lancamento(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_hora: datetime
    tipo: str
    motivo: str
    descricao_motivo: str
    forma_pagamento: FormaResumida
    valor: Decimal
    historico: str | None
    funcionario: Pessoa | None
    documento: str | None
    usuario: Pessoa
    estornado_em: datetime | None
    estornado_por: Pessoa | None


class LancamentoDados(BaseModel):
    motivo: Motivo
    valor: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    forma_pagamento_id: int | None = Field(default=None, description="Vazio: dinheiro")
    historico: str | None = Field(default=None, max_length=80)
    funcionario_id: int | None = Field(default=None, description="Obrigatório no vale e na comissão")

    @field_validator("historico", mode="before")
    @classmethod
    def _historico(cls, v: object) -> object:
        return _vazio_para_none(v)


class Total(BaseModel):
    """Saldo de uma forma no caixa: fundo + entradas − saídas."""

    forma_pagamento: FormaResumida
    entradas: Decimal
    saidas: Decimal
    saldo: Decimal


class Conferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    forma_pagamento: FormaResumida
    esperado: Decimal
    contado: Decimal
    diferenca: Decimal


class CaixaResumido(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class Sessao(SessaoResumo):
    caixa: CaixaResumido
    caixa_id: int
    observacao: str | None
    lancamentos: list[Lancamento]
    totais: list[Total] | None = Field(default=None, description="Só para quem confere o caixa, ou depois de fechado")
    conferencia: list[Conferencia]


class PedidoAbertura(BaseModel):
    fundo: Decimal = Field(default=Decimal(0), ge=0, max_digits=14, decimal_places=2)


class Contagem(BaseModel):
    forma_pagamento_id: int
    contado: Decimal = Field(ge=0, max_digits=14, decimal_places=2)


class PedidoFechamento(BaseModel):
    contagem: list[Contagem] = Field(description="O que foi contado em cada forma; a que não vier conta como zero")
    observacao: str | None = Field(default=None, max_length=2000)


class PaginaSessoes(BaseModel):
    itens: list[SessaoResumo]
    total: int
