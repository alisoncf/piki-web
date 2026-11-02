from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.dominios.caixa.esquemas import FormaResumida, Pessoa
from app.nucleo.documentos import cpf_valido, so_digitos


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


class ConsumidorDados(BaseModel):
    """Quem compra sem cadastro: o nome é obrigatório para fechar; o resto, se a pessoa quiser dar."""

    nome: str | None = Field(default=None, max_length=60)
    cpf: str | None = None
    dia_nascimento: int | None = Field(default=None, ge=1, le=31)
    mes_nascimento: int | None = Field(default=None, ge=1, le=12)
    telefone: str | None = None
    email: str | None = Field(default=None, max_length=100)

    @field_validator("nome", "email", mode="before")
    @classmethod
    def _texto(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("cpf", mode="before")
    @classmethod
    def _cpf(cls, v: object) -> str | None:
        cpf = so_digitos(v) or None
        if cpf and not cpf_valido(cpf):
            raise ValueError("CPF inválido")
        return cpf

    @field_validator("telefone", mode="before")
    @classmethod
    def _telefone(cls, v: object) -> str | None:
        numero = so_digitos(v) or None
        if numero and len(numero) not in (10, 11):
            raise ValueError("Telefone com DDD: 10 ou 11 dígitos")
        return numero

    @model_validator(mode="after")
    def _aniversario(self) -> "ConsumidorDados":
        if (self.dia_nascimento is None) != (self.mes_nascimento is None):
            raise ValueError("Informe o dia e o mês do aniversário")
        return self


class EntregaDados(BaseModel):
    taxa: Decimal = Field(default=Decimal(0), ge=0, max_digits=14, decimal_places=2, description="Entra no total, sem desconto")
    cep: str | None = None
    logradouro: str | None = Field(default=None, max_length=100)
    numero: str | None = Field(default=None, max_length=20)
    complemento: str | None = Field(default=None, max_length=60)
    bairro: str | None = Field(default=None, max_length=60)
    cidade_id: int | None = None
    ponto_referencia: str | None = Field(default=None, max_length=60)
    telefone: str | None = None

    @field_validator("logradouro", "numero", "complemento", "bairro", "ponto_referencia", mode="before")
    @classmethod
    def _texto(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("cep", "telefone", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> str | None:
        return so_digitos(v) or None


class VendaDados(ComAutorizacao):
    cliente_id: int | None = None
    consumidor: ConsumidorDados | None = Field(default=None, description="Sem cliente cadastrado: quem comprou")
    entrega: EntregaDados | None = Field(default=None, description="Venda com entrega; null tira a entrega")
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


class PedidoRecebimento(ComAutorizacao):
    sessao_caixa_id: int
    valor_recebido: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2,
                                           description="No dinheiro, o que o cliente deu (para o troco)")
    # só no crediário
    entrada: Decimal = Field(default=Decimal(0), ge=0, max_digits=14, decimal_places=2,
                             description="Crediário: o que o cliente paga na hora; o resto vira o carnê")
    forma_entrada_id: int | None = Field(default=None, description="Crediário: a forma em que a entrada foi paga")
    primeiro_vencimento: date | None = Field(default=None, description="Crediário: sem ele, um mês depois de hoje")


class PedidoCancelamento(BaseModel):
    motivo: str = Field(min_length=1, max_length=200)

    @field_validator("motivo", mode="before")
    @classmethod
    def _motivo(cls, v: object) -> object:
        return _vazio_para_none(v)


class CidadeResumida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    uf: str


class SetorDoCliente(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    cidade: CidadeResumida | None


class TelefoneDoCliente(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero: str


class ClienteResumido(BaseModel):
    """O cliente cadastrado na venda, com o endereço para preencher a entrega."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf_cnpj: str | None
    bloqueado: bool
    cep: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    ponto_referencia: str | None = None
    setor: SetorDoCliente | None = None
    telefones: list[TelefoneDoCliente] = []


class Consumidor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str | None
    dia_nascimento: int | None
    mes_nascimento: int | None
    telefone: str | None
    email: str | None


class Entrega(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    taxa: Decimal
    cep: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    cidade: CidadeResumida | None
    ponto_referencia: str | None
    telefone: str | None


class BuscaPorCpf(BaseModel):
    """O que já se sabe de quem tem este CPF: cliente cadastrado ou consumidor de outra compra."""

    cliente: ClienteResumido | None
    consumidor: Consumidor | None


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
    em_queima: bool
    disponivel: Decimal | None = Field(default=None, description="Estoque da loja, para avisar quando falta")


class SessaoDoCaixa(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    caixa: Pessoa


class Credito(BaseModel):
    """O crédito do cliente no crediário: o limite menos o que está em aberto em todas as lojas."""

    model_config = ConfigDict(from_attributes=True)

    limite: Decimal
    em_aberto: Decimal
    disponivel: Decimal
    impedimento: str | None = Field(description="Bloqueado ou com o crédito suspenso: não compra no crediário")


class Parcela(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero: int
    vencimento: date
    valor: Decimal
    aberto: Decimal


class Carne(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    valor: Decimal
    parcelas: list[Parcela]


class VendaResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    situacao: str
    criado_em: datetime
    vence_em: datetime
    vendedor: Pessoa
    comprador: str | None = Field(description="O nome pelo qual o caixa acha a venda")
    cliente: ClienteResumido | None
    forma_pagamento: FormaResumida | None
    parcelas: int
    total: Decimal


class Venda(VendaResumo):
    percentual_desconto: Decimal
    subtotal: Decimal
    desconto: Decimal
    observacao: str | None
    consumidor: Consumidor | None
    entrega: Entrega | None
    taxa_entrega: Decimal
    fechada_em: datetime | None
    desconto_autorizado_por: Pessoa | None
    parcelas_autorizadas_por: Pessoa | None
    itens: list[Item]
    sessao_caixa: SessaoDoCaixa | None
    recebida_em: datetime | None
    recebida_por: Pessoa | None
    valor_recebido: Decimal | None
    troco: Decimal | None
    entrada: Decimal | None
    forma_entrada: FormaResumida | None
    limite_autorizado_por: Pessoa | None
    carne: Carne | None = Field(default=None, description="Crediário recebido: as parcelas")
    credito: Credito | None = Field(default=None, description="Venda aberta no crediário: o crédito do cliente")
    cancelada_em: datetime | None
    cancelada_por: Pessoa | None
    motivo_cancelamento: str | None
    avisos: list[str] = Field(default=[], description="Ao receber: produtos que ficaram com estoque negativo")


class LojaDoCarne(BaseModel):
    nome: str
    cnpj: str | None
    endereco: str
    telefone: str | None


class ClienteDoCarne(BaseModel):
    id: int
    nome: str
    cpf_cnpj: str | None
    endereco: str
    cidade: str


class ImpressaoCarne(BaseModel):
    """O que vai no carnê impresso."""

    loja: LojaDoCarne
    venda: int
    data: datetime
    cliente: ClienteDoCarne
    carne: Carne


class PaginaVendas(BaseModel):
    itens: list[VendaResumo]
    total: int
