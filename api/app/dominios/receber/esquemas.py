from datetime import date, datetime
from decimal import Decimal
from typing import Literal

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
    venda: int | None  # o número da venda na loja (das vendas do sistema novo)
    documento: str = Field(description="Loja e número: 01-0001234 (o do VB6 se repete entre as lojas)")
    origem: str = Field(description="venda, acerto (de consignação) ou avulso")
    numero: int
    parcelas: int
    vencimento: date
    valor: Decimal
    aberto: Decimal
    dias_atraso: int
    juros: Decimal = Field(description="Sugerido: % ao mês da forma Crediário, por dia de atraso, sobre o que falta")
    prejuizo: bool
    conta_cobranca: str


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
    voltar_para_geral: bool = Field(
        default=False, description="Os carnês das parcelas recebidas voltam para a conta de cobrança Geral (a loja)")
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
    quitou: bool = Field(default=False, description="Depois deste recebimento, o cliente não deve mais nada")


class ClienteDaParcela(BaseModel):
    id: int
    nome: str
    cpf_cnpj: str | None
    bloqueado: bool
    credito_suspenso: bool


class LinhaParcela(BaseModel):
    """Uma parcela na consulta das contas a receber."""

    id: int
    conta_id: int
    documento: str
    numero_documento: str | None = Field(description="O número do documento, sem a loja (o do VB6)")
    origem: str
    loja: LojaResumida
    cliente: ClienteDaParcela
    setor: str | None
    cidade: str | None
    historico: str
    emissao: date
    numero: int
    parcelas: int
    vencimento: date
    vencimento_inicial: date | None
    valor: Decimal
    aberto: Decimal
    dias_atraso: int
    juros: Decimal
    prejuizo: bool
    conta_cobranca: str
    tipo_cobranca: str | None
    prejuizo_em: datetime | None
    prejuizo_por: str | None
    prejuizo_motivo: str | None


class PedidoPrejuizo(BaseModel):
    parcelas: list[int] = Field(min_length=1)
    motivo: str | None = Field(default=None, max_length=200, description="Para marcar: por que caiu no prejuízo")


class PaginaParcelas(BaseModel):
    itens: list[LinhaParcela]
    total: int
    soma_valor: Decimal
    soma_aberto: Decimal
    juros_ao_mes: Decimal


class ContaCobranca(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    padrao: bool
    ativo: bool


class ContaCobrancaDados(BaseModel):
    nome: str = Field(min_length=1, max_length=40)
    ativo: bool = True


class PedidoCobranca(BaseModel):
    parcelas: list[int] = Field(min_length=1)
    conta_cobranca_id: int


class PedidoProrrogacao(BaseModel):
    parcelas: list[int] = Field(min_length=1)
    vencimento: date | None = Field(default=None, description="O novo vencimento, igual para todas")
    dias: int | None = Field(default=None, ge=1, le=3650, description="Ou: tantos dias depois do vencimento de cada uma")
    anotacao: str | None = Field(default=None, max_length=500, description="O que o cliente disse no contato")


class ParcelaDados(BaseModel):
    tipo_cobranca: Literal["loja", "cliente", "representante", "deposito", "boleto"] | None = None
    conta_cobranca_id: int


class DocumentoDados(BaseModel):
    historico: str = Field(min_length=1, max_length=80)
    documento: str | None = Field(default=None, max_length=20, description="O número do documento")


class Mudanca(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mudanca: str
    de: str | None
    para: str | None
    anotacao: str | None
    data_hora: datetime
    usuario: Pessoa | None


class PedidoBloqueio(BaseModel):
    clientes: list[int] = Field(min_length=1)
    bloquear: bool


class ClienteAchado(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf_cnpj: str | None


class Achado(BaseModel):
    como: str = Field(description="cliente, documento ou parcela: como a busca achou")
    cliente: ClienteAchado
    conta_id: int | None = None
    documento: str | None = Field(default=None, description="Loja e número do documento achado")
    parcela_id: int | None = None
    parcela: str | None = Field(default=None, description="A parcela achada: 2/5, vencimento e valor")
