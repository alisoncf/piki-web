from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.nucleo.documentos import so_digitos


class EstoqueDados(BaseModel):
    """O que se altera no produto na loja: onde fica e os impostos do regime da empresa."""

    localizacao: str | None = Field(default=None, max_length=30)
    cst_csosn: str | None = Field(default=None, pattern=r"^\d{2,3}$", description="CST (2 dígitos) ou CSOSN (3) do ICMS")
    cfop: str | None = Field(default=None, pattern=r"^\d{4}$")
    aliquota_icms: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)

    @field_validator("localizacao", mode="before")
    @classmethod
    def _limpar(cls, v: object) -> object:
        return (v.strip() or None) if isinstance(v, str) else v

    @field_validator("cst_csosn", "cfop", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> str | None:
        return so_digitos(v) or None


class Estoque(EstoqueDados):
    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    quantidade: Decimal
    reservado: Decimal = Field(description="Com os representantes (consignação)")
    disponivel: Decimal = Field(description="Na loja: quantidade menos o reservado")


class PedidoAjuste(BaseModel):
    quantidade: Decimal = Field(max_digits=14, decimal_places=3, description="A quantidade certa, contada")
    motivo: str = Field(min_length=3, max_length=200)

    @field_validator("motivo", mode="before")
    @classmethod
    def _motivo(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class UsuarioDoMovimento(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class Movimento(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_hora: datetime
    tipo: str
    descricao: str = Field(description="O nome do tipo: Venda, Ajuste...")
    quantidade: Decimal
    reservado: Decimal
    saldo: Decimal
    saldo_reservado: Decimal
    documento: str | None
    observacao: str | None
    usuario: UsuarioDoMovimento | None


class PaginaMovimentos(BaseModel):
    itens: list[Movimento]
    total: int
