from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.nucleo.documentos import so_digitos


def _vazio_para_none(valor: object) -> object:
    if isinstance(valor, str):
        return valor.strip() or None
    return valor


class NomeDados(BaseModel):
    """Seção e marca: só nome e situação."""

    nome: str = Field(min_length=1, max_length=50)
    ativo: bool = True

    @field_validator("nome", mode="before")
    @classmethod
    def _nome(cls, v: object) -> object:
        return _vazio_para_none(v)


class Marca(NomeDados):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SubsecaoDados(NomeDados):
    secao_id: int


class SecaoSimples(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class Subsecao(SubsecaoDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    secao: SecaoSimples


class SubsecaoDaSecao(NomeDados):
    model_config = ConfigDict(from_attributes=True)

    id: int


class Secao(NomeDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subsecoes: list[SubsecaoDaSecao]


class FornecedorDoProduto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fornecedor_id: int
    codigo: str | None = Field(default=None, max_length=60, description="O código do produto para o fornecedor")

    @field_validator("codigo", mode="before")
    @classmethod
    def _codigo(cls, v: object) -> object:
        return _vazio_para_none(v)


class FornecedorResumido(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    nome_fantasia: str | None


class FornecedorDoProdutoCompleto(FornecedorDoProduto):
    fornecedor: FornecedorResumido


class Foto(BaseModel):
    """Foto do produto, sem o arquivo (que vem por /produtos/{id}/fotos/{id}/arquivo)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ordem: int
    tamanho: int


class ProdutoDados(BaseModel):
    """O que se envia para criar ou alterar um produto. Custo, margem e preços pedem produtos.precos."""

    nome: str = Field(min_length=1, max_length=120)
    subsecao_id: int
    marca_id: int | None = None
    unidade: str = Field(default="UN", pattern=r"^[A-Z0-9]{1,6}$", description="UN, M2, M, KG, JG...")
    fracionado: bool = Field(default=False, description="Aceita quantidade com fração na venda")

    custo: Decimal = Field(default=Decimal(0), ge=0, max_digits=14, decimal_places=2)
    margem: Decimal = Field(default=Decimal(0), ge=0, max_digits=7, decimal_places=2, description="Em %")
    preco_venda: Decimal = Field(default=Decimal(0), ge=0, max_digits=14, decimal_places=2)
    preco_queima: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)

    ncm: str | None = Field(default=None, pattern=r"^\d{8}$")
    cest: str | None = Field(default=None, pattern=r"^\d{7}$")
    origem: int = Field(default=0, ge=0, le=8, description="Origem da mercadoria na NF-e (0 nacional)")

    observacao: str | None = Field(default=None, max_length=4000)
    ativo: bool = True

    codigos_barras: list[str] = Field(default=[], description="Códigos de fábrica (EAN...), só dígitos, de 8 a 14")
    fornecedores: list[FornecedorDoProduto] = []

    @field_validator("nome", "observacao", mode="before")
    @classmethod
    def _limpar(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("unidade", mode="before")
    @classmethod
    def _unidade(cls, v: object) -> object:
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("ncm", "cest", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> str | None:
        return so_digitos(v) or None

    @field_validator("codigos_barras", mode="before")
    @classmethod
    def _barras(cls, v: object) -> object:
        return [so_digitos(c) for c in v if so_digitos(c)] if isinstance(v, list) else v


class ProdutoResumo(BaseModel):
    """Uma linha da lista de produtos."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    nome: str
    subsecao: Subsecao | None
    marca: Marca | None
    unidade: str
    preco_venda: Decimal
    preco_queima: Decimal | None
    ativo: bool
    fornecedor: str | None = Field(description="Nome (fantasia, se houver) do primeiro fornecedor")
    foto_id: int | None = Field(description="A foto principal")
    estoque: Decimal | None = Field(default=None, description="Saldo na loja ativa (só para quem tem estoque.ver)")


class PaginaProdutos(BaseModel):
    itens: list[ProdutoResumo]
    total: int


class Produto(ProdutoDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    subsecao_id: int | None  # importado do VB6 sem subseção válida
    subsecao: Subsecao | None
    marca: Marca | None
    fornecedores: list[FornecedorDoProdutoCompleto]
    fotos: list[Foto]
    criado_em: datetime
    atualizado_em: datetime

    @field_validator("codigos_barras", mode="before")
    @classmethod
    def _barras(cls, v: object) -> object:
        return [getattr(c, "codigo", c) for c in v]
