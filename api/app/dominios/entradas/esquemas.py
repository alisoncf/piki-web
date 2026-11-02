from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProdutoDoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    nome: str
    unidade: str
    fracionado: bool
    custo: Decimal
    margem: Decimal
    preco_venda: Decimal


class Item(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    codigo: str = Field(description="O código do produto para o fornecedor")
    ean: str | None
    descricao: str
    ncm: str | None
    cest: str | None
    cfop: str | None
    unidade: str
    quantidade: Decimal
    valor_unitario: Decimal
    valor_produtos: Decimal
    valor_custo: Decimal = Field(description="Produtos − desconto + frete, seguro, outras despesas, IPI e ST")
    embalagem: int
    unidades: Decimal = Field(description="Quantas unidades do produto entram no estoque")
    custo_unitario: Decimal | None
    preco_venda: Decimal | None = Field(description="Preço novo, se for mudar ao confirmar")
    produto: ProdutoDoItem | None


class FornecedorDaNota(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    nome_fantasia: str | None
    cpf_cnpj: str


class UsuarioDaNota(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class NotaResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chave: str
    numero: int
    serie: int
    data_emissao: datetime
    valor_total: Decimal
    situacao: str
    fornecedor: FornecedorDaNota
    criado_em: datetime
    confirmada_em: datetime | None


class Nota(NotaResumo):
    usuario: UsuarioDaNota | None
    confirmada_por: UsuarioDaNota | None
    itens: list[Item]
    fornecedor_novo: bool = Field(default=False, description="O fornecedor foi cadastrado agora, com os dados do XML")


class PaginaNotas(BaseModel):
    itens: list[NotaResumo]
    total: int


class ItemDados(BaseModel):
    """O que a loja decide em cada item: o produto, a embalagem e, se for mudar, o preço de venda."""

    produto_id: int | None
    embalagem: int = Field(default=1, ge=1, le=10000)
    preco_venda: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
