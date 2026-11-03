from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dominios.cidades.esquemas import Cidade
from app.nucleo.documentos import so_digitos

_COR = r"^#[0-9a-f]{6}$"


class Tema(BaseModel):
    """Esquema de cores da empresa na tela. Botões e links continuam na cor da marca (D14)."""

    principal: str = Field(pattern=_COR, description="Faixa do cabeçalho, selo e troca de empresa")
    fundo: str = Field(pattern=_COR, description="Fundo das telas")
    menu: str = Field(pattern=_COR, description="Fundo do menu lateral")

    @field_validator("principal", "fundo", "menu", mode="before")
    @classmethod
    def _minusculas(cls, v: object) -> object:
        return v.strip().lower() if isinstance(v, str) else v


class EmpresaResumo(BaseModel):
    """O que a sessão e as listas precisam saber da empresa."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nome: str
    tema: Tema = Field(validation_alias="tema_efetivo")


def _vazio_para_none(v: object) -> object:
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


class EmpresaDados(BaseModel):
    """O que se altera na ficha da empresa. O código não muda depois de criado."""

    nome: str = Field(min_length=1, max_length=60, description="Nome curto, mostrado na escolha de empresa")
    razao_social: str | None = Field(default=None, max_length=100)
    nome_fantasia: str | None = Field(default=None, max_length=60)
    cnpj: str | None = Field(default=None, pattern=r"^\d{14}$")
    inscricao_estadual: str | None = Field(default=None, max_length=20)
    inscricao_municipal: str | None = Field(default=None, max_length=20)
    suframa: str | None = Field(default=None, max_length=19)
    crt: str | None = Field(default=None, pattern="^[123]$")
    sped_perfil: str | None = Field(default=None, pattern="^[ABC]$")
    sped_atividade: str | None = Field(default=None, pattern="^[01]$")
    cep: str | None = Field(default=None, pattern=r"^\d{8}$")
    logradouro: str | None = Field(default=None, max_length=60)
    numero: str | None = Field(default=None, max_length=10)
    complemento: str | None = Field(default=None, max_length=60)
    bairro: str | None = Field(default=None, max_length=60)
    cidade_id: int | None = None
    telefone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=200)
    ativa: bool = True
    tema: Tema | None = Field(default=None, description="Vazio: esquema automático pelo código da empresa")

    @field_validator("cnpj", "cep", "telefone", "inscricao_estadual", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> object:
        return (so_digitos(v) or None) if isinstance(v, str) else v

    @field_validator(
        "razao_social", "nome_fantasia", "inscricao_municipal", "suframa", "crt", "sped_perfil", "sped_atividade",
        "logradouro", "numero", "complemento", "bairro", "email", mode="before",
    )
    @classmethod
    def _limpar(cls, v: object) -> object:
        return _vazio_para_none(v)


class EmpresaNova(EmpresaDados):
    codigo: str = Field(pattern=r"^\d{2}$", description="Código da filial (01, 02...), o mesmo do VB6")


class Empresa(EmpresaResumo, EmpresaDados):
    """A ficha completa. `tema` é sempre o esquema em uso, mesmo o automático."""

    cidade: Cidade | None
    imagens: list[str] = Field(validation_alias="tipos_de_imagem", description="Imagens enviadas: logo, qrcode")


class Certificado(BaseModel):
    titular: str | None
    validade: datetime | None
    dias_para_vencer: int | None


class Fiscal(BaseModel):
    """Os dados das notas fiscais da empresa. A senha do certificado e o token do CSC nunca saem da API."""

    ambiente: str = Field(description="1 produção, 2 homologação")
    certificado: Certificado | None
    csc_id: str | None
    tem_csc: bool


class FiscalDados(BaseModel):
    ambiente: Literal["1", "2"]
    csc_id: str | None = Field(default=None, max_length=10)
    csc_token: str | None = Field(default=None, max_length=50, description="Só para trocar; vazio mantém o que está")


class CertificadoDados(BaseModel):
    arquivo: str = Field(description="O .pfx em base64")
    senha: str = Field(min_length=1, max_length=100)
