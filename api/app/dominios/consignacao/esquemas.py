from datetime import date, datetime
from decimal import Decimal

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dominios.cidades.esquemas import SetorResumo
from app.dominios.funcionarios.esquemas import Telefone
from app.nucleo.documentos import so_digitos


class ClienteDoRepresentante(BaseModel):
    """Os dados pessoais do representante, que são os da ficha de cliente dele."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf_cnpj: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    cep: str | None
    email: str | None
    setor: SetorResumo | None
    telefones: list[Telefone]


class RepresentanteResumo(BaseModel):
    """Uma linha da lista de representantes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    cliente: ClienteDoRepresentante
    ativo: bool
    bloqueado: bool
    limite: Decimal


class RepresentanteDados(BaseModel):
    """O que se edita com representantes.editar (o limite, o bloqueio e as comissões são à parte)."""

    ativo: bool = True
    lembrete: str | None = None
    lembrete_acerto: str | None = None
    observacao: str | None = None
    ultima_conferencia: date | None = None
    avalista_nome: str | None = Field(default=None, max_length=100)
    avalista_cpf: str | None = Field(default=None, max_length=14)
    avalista_rg: str | None = Field(default=None, max_length=20)
    avalista_endereco: str | None = Field(default=None, max_length=200)
    avalista_telefones: str | None = Field(default=None, max_length=200)
    avalista_anotacoes: str | None = None

    @field_validator("avalista_cpf")
    @classmethod
    def _digitos(cls, valor: str | None) -> str | None:
        return so_digitos(valor) or None if valor else None


class RepresentanteNovo(RepresentanteDados):
    cliente_id: int = Field(description="O cliente que passa a ser representante")


class ComissaoDados(BaseModel):
    tipo_cobranca: str
    percentual: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2,
                                       description="Sem ele, vale a comissão padrão do tipo")


class LimitesDados(BaseModel):
    """O que pede representantes.limites: limite, bloqueio e comissões."""

    limite: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    bloqueado: bool
    motivo_bloqueio: str | None = None
    bloqueia_impressao: bool = False
    bloqueia_devolucao: bool = False
    comissoes: list[ComissaoDados] = []


class SenhaDados(BaseModel):
    senha: str = Field(min_length=4, max_length=20)


class Comissao(BaseModel):
    tipo_cobranca: str
    nome: str
    percentual: Decimal
    padrao: bool  # vale a do tipo, o representante não tem uma própria
    percentual_padrao: Decimal


class Representante(RepresentanteResumo):
    motivo_bloqueio: str | None
    tem_senha: bool
    bloqueia_impressao: bool
    bloqueia_devolucao: bool
    lembrete: str | None
    lembrete_acerto: str | None
    observacao: str | None
    ultima_conferencia: date | None
    data_cadastro: date
    avalista_nome: str | None
    avalista_cpf: str | None
    avalista_rg: str | None
    avalista_endereco: str | None
    avalista_telefones: str | None
    avalista_anotacoes: str | None
    comissoes: list[Comissao]


class ItemPosicao(BaseModel):
    produto_id: int
    codigo: int
    descricao: str
    quantidade: Decimal
    total_transferencia: Decimal
    total_atual: Decimal


class Posicao(BaseModel):
    """O estoque consignado do representante na loja: o "em uso" é pelo preço da transferência (o que conta no
    limite); mostra também pelo preço atual."""

    limite: Decimal
    em_uso: Decimal
    em_uso_atual: Decimal
    disponivel: Decimal
    pecas: Decimal
    itens: list[ItemPosicao]


class RepresentanteDaTransferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    cliente: ClienteDoRepresentante
    bloqueado: bool
    lembrete: str | None
    lembrete_acerto: str | None


class Pessoa(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class ProdutoDoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    unidade: str
    fracionado: bool


class ItemTransferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ordem: int
    produto: ProdutoDoItem
    descricao: str
    quantidade: Decimal
    preco: Decimal
    total: Decimal
    restante: Decimal


class Transferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    situacao: str
    representante: RepresentanteDaTransferencia
    total: Decimal
    atendida_por: Pessoa
    criado_em: datetime
    confirmada_em: datetime | None
    itens: list[ItemTransferencia]
    avisos: list[str] = []


class TransferenciaNova(BaseModel):
    representante_id: int


class ItemNovo(BaseModel):
    produto_id: int
    quantidade: Decimal = Field(default=Decimal("1"), gt=0, max_digits=14, decimal_places=3)


class QuantidadeDados(BaseModel):
    quantidade: Decimal = Field(ge=0, max_digits=14, decimal_places=3, description="Zero tira o item")


class Confirmacao(BaseModel):
    senha: str = Field(min_length=1, max_length=20, description="A senha do representante")


class TransferenciaDoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    confirmada_em: datetime | None


class ItemComEle(BaseModel):
    """Um item de transferência que ainda tem resto com o representante: de onde a peça devolvida (ou acertada) sai."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transferencia: TransferenciaDoItem
    produto: ProdutoDoItem
    descricao: str
    preco: Decimal
    quantidade: Decimal
    restante: Decimal


class ItemDevolucao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ordem: int
    item_transferencia: ItemComEle
    quantidade: Decimal
    total: Decimal


class Devolucao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    situacao: str
    retificadora: bool
    observacao: str | None
    representante: RepresentanteDaTransferencia
    total: Decimal
    atendida_por: Pessoa
    autorizada_por: Pessoa | None
    criado_em: datetime
    confirmada_em: datetime | None
    itens: list[ItemDevolucao]


class DevolucaoNova(BaseModel):
    representante_id: int


class DevolucaoDados(BaseModel):
    retificadora: bool = False
    observacao: str | None = Field(default=None, max_length=200)


class ItemDevolucaoNovo(BaseModel):
    item_transferencia_id: int = Field(description="O item de transferência de onde a peça volta (GET .../com-ele)")
    quantidade: Decimal = Field(default=Decimal("1"), gt=0, max_digits=14, decimal_places=3)


class Liberacao(BaseModel):
    login: str = Field(min_length=1, max_length=30)
    senha: str = Field(min_length=1, max_length=200)


class ConfirmacaoDevolucao(Confirmacao):
    liberacao: Liberacao | None = Field(default=None, description="O gerente, se a devolução do representante está bloqueada")


class AcertoNovo(BaseModel):
    representante_id: int


class AcertoDados(BaseModel):
    """O que se escolhe no acerto aberto. O % da comissão vem do representante, pelo tipo."""

    para: Literal["cliente", "representante"] = "cliente"
    cliente_id: int | None = Field(default=None, description="O cliente do representante (no acerto para o cliente)")
    queima: bool = Field(default=False, description="Só produtos em queima, pelo preço de queima; à vista, para ele")
    pagamento: Literal["prazo", "vista"] = "prazo"
    tipo_comissao: str | None = Field(default=None, description=(
        "A prazo, o tipo de cobrança; à vista, vista_dinheiro, vista_cartao ou vista_parcelado"))
    negociado: Decimal | None = Field(default=None, max_digits=14, decimal_places=2,
                                      description="O valor por que o representante vendeu; a diferença fica para ele")
    parcelas: int = Field(default=1, ge=1, le=36)
    primeiro_vencimento: date | None = None


class ClienteDoAcerto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf_cnpj: str | None


class ItemAcerto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ordem: int
    item_transferencia: ItemComEle
    quantidade: Decimal
    preco: Decimal
    total: Decimal


class FormaDoPagamento(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo: str


class PagamentoAcerto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    forma_pagamento: FormaDoPagamento
    valor: Decimal
    parcelas: int


class ParcelaDoAcerto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    vencimento: date
    valor: Decimal
    comissao: Decimal = Decimal("0.00")


class Acerto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    situacao: str
    representante: RepresentanteDaTransferencia
    para: str
    cliente: ClienteDoAcerto | None
    queima: bool
    pagamento: str
    tipo_comissao: str
    nome_comissao: str = ""
    percentual: Decimal
    total_inicial: Decimal
    diferenca: Decimal
    negociado: Decimal
    comissao: Decimal
    valor: Decimal
    entrada: Decimal
    a_prazo: Decimal
    parcelas: int
    primeiro_vencimento: date | None
    atendida_por: Pessoa
    autorizada_por: Pessoa | None
    criado_em: datetime
    confirmada_em: datetime | None
    itens: list[ItemAcerto]
    pagamentos: list[PagamentoAcerto]
    carne: list[ParcelaDoAcerto] = []  # depois de confirmado, as parcelas geradas
    conta_id: int | None = None


class ItemAcertoNovo(BaseModel):
    item_transferencia_id: int = Field(description="O item de transferência de onde a peça sai (GET .../com-ele)")
    quantidade: Decimal = Field(default=Decimal("1"), gt=0, max_digits=14, decimal_places=3)


class PagamentoDados(BaseModel):
    forma_pagamento_id: int
    valor: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    parcelas: int = Field(default=1, ge=1, le=36)


class ConfirmacaoAcerto(BaseModel):
    sessao_caixa_id: int = Field(description="O caixa do consignado, aberto")
    pagamentos: list[PagamentoDados] = Field(default=[], description="À vista, tudo; a prazo, a entrada (se tiver)")
    autorizacao: Liberacao | None = Field(default=None, description="A gerência, se o carnê passa do limite")


class LinhaComissao(BaseModel):
    id: int
    acerto: str | None
    data_acerto: date | None
    cliente: str | None
    parcela: str | None
    vencimento: date
    valor_parcela: Decimal | None
    falta_na_parcela: Decimal | None  # só das parcelas que estão no sistema
    valor: Decimal
    pago: Decimal
    situacao: str
    liberada: bool


class RelatorioComissoes(BaseModel):
    comissao: Decimal
    pago: Decimal
    liberado: Decimal  # o saldo que já pode ser pago
    a_vencer: Decimal
    quantas: int  # as linhas do filtro; a lista vem limitada
    linhas: list[LinhaComissao]


class PagamentoComissaoDados(BaseModel):
    valor: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    forma_pagamento_id: int
    sessao_caixa_id: int
    de: date | None = None  # o período do relatório: só baixa as comissões dele
    ate: date | None = None


class PagamentoComissao(BaseModel):
    id: int
    data_hora: datetime
    valor: Decimal
    forma: str | None
    usuario: str | None
    estornado_em: datetime | None
    estornado_por: str | None
    do_vb6: bool


class LinhaDoPagamento(LinhaComissao):
    baixado: Decimal


class ComprovanteComissao(PagamentoComissao):
    representante: RepresentanteResumo
    linhas: list[LinhaDoPagamento]
