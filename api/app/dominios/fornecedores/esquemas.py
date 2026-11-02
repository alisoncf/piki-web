from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dominios.cidades.esquemas import Cidade
from app.dominios.funcionarios.esquemas import Telefone
from app.nucleo.documentos import so_digitos


def _vazio_para_none(valor: object) -> object:
    if isinstance(valor, str):
        return valor.strip() or None
    return valor


class Contato(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str = Field(min_length=1, max_length=60)
    funcao: str | None = Field(default=None, max_length=40, description="Representante, financeiro, vendas...")
    telefone: str | None = Field(default=None, min_length=8, max_length=15, description="Só dígitos, com DDD")
    email: str | None = Field(default=None, max_length=200)

    @field_validator("nome", "funcao", "email", mode="before")
    @classmethod
    def _limpar(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("telefone", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> str | None:
        return so_digitos(v) or None


class FornecedorDados(BaseModel):
    """O que se envia para criar ou alterar um fornecedor."""

    nome: str = Field(min_length=1, max_length=100, description="Razão social, ou o nome se for pessoa física")
    nome_fantasia: str | None = Field(default=None, max_length=60)
    cpf_cnpj: str = Field(description="CNPJ ou CPF válido; só dígitos")
    inscricao_estadual: str | None = Field(default=None, max_length=20)

    cep: str | None = Field(default=None, pattern=r"^\d{8}$")
    logradouro: str | None = Field(default=None, max_length=60)
    numero: str | None = Field(default=None, max_length=10)
    complemento: str | None = Field(default=None, max_length=60)
    bairro: str | None = Field(default=None, max_length=60)
    cidade_id: int | None = None

    email: str | None = Field(default=None, max_length=200)
    site: str | None = Field(default=None, max_length=200)
    observacao: str | None = Field(default=None, max_length=4000)
    ativo: bool = True

    telefones: list[Telefone] = []
    contatos: list[Contato] = []

    @field_validator(
        "nome", "nome_fantasia", "inscricao_estadual", "logradouro", "numero", "complemento", "bairro",
        "email", "site", "observacao", mode="before",
    )
    @classmethod
    def _limpar(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("cpf_cnpj", mode="before")
    @classmethod
    def _documento(cls, v: object) -> str:
        return so_digitos(v)

    @field_validator("cep", mode="before")
    @classmethod
    def _cep(cls, v: object) -> str | None:
        return so_digitos(v) or None


class FornecedorResumo(BaseModel):
    """Uma linha da lista de fornecedores."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    nome_fantasia: str | None
    cpf_cnpj: str
    tipo: str = Field(description="F pessoa física, J pessoa jurídica")
    cidade: Cidade | None
    ativo: bool


class Fornecedor(FornecedorDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    cidade: Cidade | None


class DadosDoCnpj(BaseModel):
    """O cadastro público do CNPJ (BrasilAPI), para preencher a ficha."""

    cnpj: str
    razao_social: str | None
    nome_fantasia: str | None
    situacao: str | None = Field(description="Situação na Receita: ATIVA, BAIXADA, INAPTA...")
    cep: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    cidade: Cidade | None = Field(description="Pelo código do IBGE; vazia se o município não está na lista")
    telefones: list[str] = Field(description="Só dígitos, com DDD")
    email: str | None
    fornecedor_id: int | None = Field(description="Se o CNPJ já está cadastrado como fornecedor")
