from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dominios.acesso.esquemas import EmpresaResumo
from app.nucleo.documentos import TIPOS_TELEFONE, so_digitos


def _vazio_para_none(valor: object) -> object:
    if isinstance(valor, str):
        return valor.strip() or None
    return valor


class CargoDados(BaseModel):
    nome: str = Field(min_length=1, max_length=40)
    vende: bool = False
    cobra: bool = False
    ativo: bool = True

    @field_validator("nome", mode="before")
    @classmethod
    def _nome(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class Cargo(CargoDados):
    model_config = ConfigDict(from_attributes=True)

    id: int


class Telefone(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero: str = Field(min_length=8, max_length=15, description="Só dígitos, com DDD")
    tipo: str = Field(description="Código do tipo: " + ", ".join(f"{k} {v}" for k, v in TIPOS_TELEFONE.items()))

    @field_validator("numero", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> str:
        return so_digitos(v)

    @field_validator("tipo")
    @classmethod
    def _tipo(cls, v: str) -> str:
        if v not in TIPOS_TELEFONE:
            raise ValueError("tipo de telefone inválido")
        return v


class FuncionarioDados(BaseModel):
    """O que se envia para criar ou alterar um funcionário."""

    nome: str = Field(min_length=1, max_length=80)
    apelido: str | None = Field(default=None, max_length=30)
    cpf: str | None = Field(default=None, description="Só dígitos")
    rg: str | None = Field(default=None, max_length=20)
    data_nascimento: date | None = None
    sexo: str | None = Field(default=None, pattern="^[MF]$")
    naturalidade: str | None = Field(default=None, max_length=40)

    empresa_id: int = Field(description="Loja onde trabalha")
    cargo_id: int | None = None
    ativo: bool = True
    pode_tirar_vale: bool = True
    limite_vale: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)

    cep: str | None = Field(default=None, max_length=8)
    logradouro: str | None = Field(default=None, max_length=60)
    bairro: str | None = Field(default=None, max_length=40)
    cidade: str | None = Field(default=None, max_length=40)
    uf: str | None = Field(default=None, pattern="^[A-Z]{2}$")

    conjuge: str | None = Field(default=None, max_length=60)
    pai: str | None = Field(default=None, max_length=60)
    mae: str | None = Field(default=None, max_length=60)
    endereco_pais: str | None = Field(default=None, max_length=100)
    observacao: str | None = Field(default=None, max_length=2000)

    telefones: list[Telefone] = []

    @field_validator(
        "nome", "apelido", "rg", "naturalidade", "logradouro", "bairro", "cidade", "conjuge", "pai", "mae",
        "endereco_pais", "observacao", "sexo", mode="before",
    )
    @classmethod
    def _limpar(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("cpf", "cep", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> str | None:
        return so_digitos(v) or None

    @field_validator("uf", mode="before")
    @classmethod
    def _uf(cls, v: object) -> object:
        v = _vazio_para_none(v)
        return v.upper() if isinstance(v, str) else v


class FuncionarioResumo(BaseModel):
    """Uma linha da lista de funcionários."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    apelido: str | None
    cpf: str | None
    ativo: bool
    empresa: EmpresaResumo
    cargo: Cargo | None


class Funcionario(FuncionarioDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa: EmpresaResumo
    cargo: Cargo | None
