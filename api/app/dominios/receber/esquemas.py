from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.dominios.caixa.esquemas import FormaResumida, Pessoa


class LojaResumida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nome: str


class ParcelaAberta(BaseModel):
    """Uma parcela que falta pagar, de qualquer loja, com os juros de atraso sugeridos para hoje."""

    id: int
    conta_id: int
    loja: LojaResumida  # a que vendeu
    venda: int | None  # o número da venda na loja
    numero: int
    parcelas: int
    vencimento: date
    valor: Decimal
    aberto: Decimal
    dias_atraso: int
    juros: Decimal = Field(description="Sugerido: % ao mês da forma Crediário, por dia de atraso, sobre o que falta")


class ParcelasDoCliente(BaseModel):
    juros_ao_mes: Decimal
    parcelas: list[ParcelaAberta]


class ItemDados(BaseModel):
    parcela_id: int
    valor: Decimal = Field(gt=0, max_digits=14, decimal_places=2, description="Quanto abate da parcela (pode ser parte)")
    juros: Decimal = Field(default=Decimal(0), ge=0, max_digits=14, decimal_places=2)


class PagamentoDados(BaseModel):
    forma_pagamento_id: int
    valor: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class RecebimentoDados(BaseModel):
    sessao_caixa_id: int
    cliente_id: int
    itens: list[ItemDados] = Field(min_length=1)
    pagamentos: list[PagamentoDados] = Field(min_length=1)
    valor_recebido: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2,
                                           description="No dinheiro, o que o cliente deu (para o troco)")


class ParcelaDoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    vencimento: date
    aberto: Decimal


class Item(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parcela: ParcelaDoItem
    valor: Decimal
    juros: Decimal


class Pagamento(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    forma_pagamento: FormaResumida
    valor: Decimal


class Recebimento(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa: LojaResumida
    cliente: Pessoa
    data_hora: datetime
    usuario: Pessoa
    itens: list[Item]
    pagamentos: list[Pagamento]
    total: Decimal
    valor_recebido: Decimal | None
    troco: Decimal | None
    estornado_em: datetime | None
    estornado_por: Pessoa | None
