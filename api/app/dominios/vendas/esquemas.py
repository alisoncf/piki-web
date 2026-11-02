from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.dominios.caixa.esquemas import FormaResumida, Pessoa


def _vazio_para_none(valor: object) -> object:
    if isinstance(valor, str):
        return valor.strip() or None
    return valor


class Autorizacao(BaseModel):
    """Login e senha de quem autoriza o desconto ou as parcelas acima do limite."""

    login: str = Field(min_length=1, max_length=30)
    senha: str = Field(min_length=1, max_length=200)


class ComAutorizacao(BaseModel):
    autorizacao: Autorizacao | None = None


class VendaDados(ComAutorizacao):
    cliente_id: int | None = None
    forma_pagamento_id: int | None = Field(default=None, description="Ao trocar, o desconto da forma vale para todos os itens")
    parcelas: int = Field(default=1, ge=1, le=24)
    observacao: str | None = Field(default=None, max_length=200)

    @field_validator("observacao", mode="before")
    @classmethod
    def _observacao(cls, v: object) -> object:
        return _vazio_para_none(v)


class ItemNovo(ComAutorizacao):
    produto_id: int
    quantidade: Decimal = Field(default=Decimal(1), gt=0, max_digits=14, decimal_places=3)


class ItemAlteracao(ComAutorizacao):
    quantidade: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    desconto: Decimal = Field(ge=0, max_digits=14, decimal_places=2, description="Em reais, no item todo")


class PedidoDesconto(ComAutorizacao):
    """Desconto no total, em % ou em reais; é rateado entre os itens."""

    percentual: Decimal | None = Field(default=None, ge=0, le=100, max_digits=7, decimal_places=4)
    valor: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)

    @model_validator(mode="after")
    def _um_dos_dois(self) -> "PedidoDesconto":
        if (self.percentual is None) == (self.valor is None):
            raise ValueError("Informe o desconto em % ou em reais")
        return self


class PedidoRecebimento(BaseModel):
    sessao_caixa_id: int
    valor_recebido: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2,
                                           description="No dinheiro, o que o cliente deu (para o troco)")


class PedidoCancelamento(BaseModel):
    motivo: str = Field(min_length=1, max_length=200)

    @field_validator("motivo", mode="before")
    @classmethod
    def _motivo(cls, v: object) -> object:
        return _vazio_para_none(v)


class ClienteResumido(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf_cnpj: str | None
    bloqueado: bool


class ProdutoDoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    unidade: str
    fracionado: bool


class Item(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ordem: int
    produto: ProdutoDoItem
    descricao: str
    quantidade: Decimal
    preco: Decimal
    bruto: Decimal
    desconto: Decimal
    total: Decimal
    disponivel: Decimal | None = Field(default=None, description="Estoque da loja, para avisar quando falta")


class SessaoDoCaixa(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    caixa: Pessoa


class VendaResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    situacao: str
    criado_em: datetime
    vence_em: datetime
    vendedor: Pessoa
    cliente: ClienteResumido | None
    forma_pagamento: FormaResumida | None
    parcelas: int
    total: Decimal


class Venda(VendaResumo):
    percentual_desconto: Decimal
    subtotal: Decimal
    desconto: Decimal
    observacao: str | None
    desconto_autorizado_por: Pessoa | None
    parcelas_autorizadas_por: Pessoa | None
    itens: list[Item]
    sessao_caixa: SessaoDoCaixa | None
    recebida_em: datetime | None
    recebida_por: Pessoa | None
    valor_recebido: Decimal | None
    troco: Decimal | None
    cancelada_em: datetime | None
    cancelada_por: Pessoa | None
    motivo_cancelamento: str | None
    avisos: list[str] = Field(default=[], description="Ao receber: produtos que ficaram com estoque negativo")


class PaginaVendas(BaseModel):
    itens: list[VendaResumo]
    total: int
