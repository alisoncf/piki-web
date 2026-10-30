from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dominios.acesso.esquemas import EmpresaResumo
from app.dominios.funcionarios.esquemas import Telefone
from app.nucleo.documentos import so_digitos

# lista fixa, não tabela: o sistema decide por ela onde cobrar (setor do endereço, setor do trabalho ou na loja).
# No VB6, cobranca_cli 1, 2 e 3.
FORMAS_COBRANCA: dict[str, str] = {
    "domicilio": "Em domicílio",
    "trabalho": "No trabalho",
    "loja": "Pagamento na loja",
}


def _vazio_para_none(valor: object) -> object:
    if isinstance(valor, str):
        return valor.strip() or None
    return valor


def _uf(valor: object) -> object:
    valor = _vazio_para_none(valor)
    return valor.upper() if isinstance(valor, str) else valor


class Nomeado(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class GrupoClienteDados(BaseModel):
    nome: str = Field(min_length=1, max_length=40)
    ativo: bool = True

    @field_validator("nome", mode="before")
    @classmethod
    def _nome(cls, v: object) -> object:
        return _vazio_para_none(v)


class GrupoCliente(GrupoClienteDados):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ParentescoDados(BaseModel):
    nome: str = Field(min_length=1, max_length=30)
    ativo: bool = True

    @field_validator("nome", mode="before")
    @classmethod
    def _nome(cls, v: object) -> object:
        return _vazio_para_none(v)


class Parentesco(ParentescoDados):
    model_config = ConfigDict(from_attributes=True)

    id: int


class CobradorDados(BaseModel):
    empresa_id: int
    funcionario_id: int


class Cobrador(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    empresa: EmpresaResumo
    funcionario: Nomeado


class SetorDados(BaseModel):
    nome: str = Field(min_length=1, max_length=40)
    tipo: str | None = Field(default=None, max_length=20)
    cidade: str | None = Field(default=None, max_length=40)
    uf: str | None = Field(default=None, pattern="^[A-Z]{2}$")
    ativo: bool = True
    cobradores: list[CobradorDados] = Field(default=[], description="Um cobrador por loja, no máximo")

    @field_validator("nome", "tipo", "cidade", mode="before")
    @classmethod
    def _limpar(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("uf", mode="before")
    @classmethod
    def _uf(cls, v: object) -> object:
        return _uf(v)


class SetorResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cidade: str | None


class Setor(SetorResumo):
    tipo: str | None
    uf: str | None
    ativo: bool
    cobradores: list[Cobrador]


class OrgaoDados(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    grupo_id: int | None = None
    setor_id: int | None = None
    endereco: str | None = Field(default=None, max_length=60)
    cep: str | None = Field(default=None, max_length=8)
    telefone: str | None = Field(default=None, max_length=15)
    observacao: str | None = Field(default=None, max_length=2000)
    ativo: bool = True

    @field_validator("nome", "endereco", "observacao", mode="before")
    @classmethod
    def _limpar(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("cep", "telefone", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> str | None:
        return so_digitos(v) or None


class Orgao(OrgaoDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    grupo: GrupoCliente | None
    setor: SetorResumo | None


class ReferenciaDados(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    telefone: str | None = Field(default=None, max_length=20)
    parentesco_id: int | None = None

    @field_validator("nome", mode="before")
    @classmethod
    def _limpar(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("telefone", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> str | None:
        return so_digitos(v) or None


class Referencia(ReferenciaDados):
    model_config = ConfigDict(from_attributes=True)

    parentesco: Parentesco | None


class AnotacaoDados(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)

    @field_validator("texto", mode="before")
    @classmethod
    def _texto(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class Anotacao(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    texto: str
    data_hora: datetime
    empresa: EmpresaResumo | None
    usuario: Nomeado | None


class ClienteDados(BaseModel):
    """O que se envia para criar ou alterar um cliente."""

    nome: str = Field(min_length=1, max_length=60)
    tipo: str = Field(default="F", pattern="^[FJ]$", description="F pessoa física, J jurídica")
    cpf_cnpj: str | None = Field(default=None, description="CPF ou CNPJ, só dígitos")
    rg: str | None = Field(default=None, max_length=20)
    inscricao_estadual: str | None = Field(default=None, max_length=20)
    data_nascimento: date | None = None
    sexo: str | None = Field(default=None, pattern="^[MF]$")
    pai: str | None = Field(default=None, max_length=60)
    mae: str | None = Field(default=None, max_length=60)
    email: str | None = Field(default=None, max_length=100)

    cep: str | None = Field(default=None, max_length=8)
    logradouro: str | None = Field(default=None, max_length=100)
    numero: str | None = Field(default=None, max_length=20)
    complemento: str | None = Field(default=None, max_length=60)
    bairro: str | None = Field(default=None, max_length=40)
    ponto_referencia: str | None = Field(default=None, max_length=60)
    cidade: str | None = Field(default=None, max_length=40)
    uf: str | None = Field(default=None, pattern="^[A-Z]{2}$")
    codigo_municipio: str | None = Field(default=None, pattern="^[0-9]{7}$", description="Código IBGE")
    setor_id: int | None = Field(default=None, description="Setor de cobrança")

    grupo_id: int | None = None
    orgao_id: int | None = Field(default=None, description="Onde trabalha")
    local_trabalho: str | None = Field(default=None, max_length=60)
    endereco_trabalho: str | None = Field(default=None, max_length=60)
    telefone_trabalho: str | None = Field(default=None, max_length=15)
    cep_trabalho: str | None = Field(default=None, max_length=8)
    setor_trabalho_id: int | None = None

    bloqueado: bool = Field(default=False, description="Bloqueado não compra a prazo")
    forma_cobranca: str = Field(
        default="domicilio", description="Onde cobrar: " + ", ".join(f"{k} ({v})" for k, v in FORMAS_COBRANCA.items())
    )
    limite_credito: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    credito_suspenso: bool = False
    recebe_mensagens: bool = True
    especial: bool = False
    observacao: str | None = Field(default=None, max_length=4000)

    telefones: list[Telefone] = []
    referencias: list[ReferenciaDados] = []

    @field_validator(
        "nome", "rg", "inscricao_estadual", "pai", "mae", "email", "logradouro", "numero", "complemento", "bairro",
        "ponto_referencia", "cidade", "codigo_municipio", "local_trabalho", "endereco_trabalho", "observacao", "sexo",
        mode="before",
    )
    @classmethod
    def _limpar(cls, v: object) -> object:
        return _vazio_para_none(v)

    @field_validator("cpf_cnpj", "cep", "cep_trabalho", "telefone_trabalho", mode="before")
    @classmethod
    def _digitos(cls, v: object) -> str | None:
        return so_digitos(v) or None

    @field_validator("uf", mode="before")
    @classmethod
    def _uf(cls, v: object) -> object:
        return _uf(v)

    @field_validator("forma_cobranca")
    @classmethod
    def _forma_cobranca(cls, v: str) -> str:
        if v not in FORMAS_COBRANCA:
            raise ValueError("forma de cobrança inválida")
        return v


class ClienteResumo(BaseModel):
    """Uma linha da lista de clientes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf_cnpj: str | None
    bairro: str | None
    cidade: str | None
    bloqueado: bool
    credito_suspenso: bool
    setor: SetorResumo | None


class PaginaClientes(BaseModel):
    itens: list[ClienteResumo]
    total: int


class Cliente(ClienteDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data_cadastro: date
    data_alteracao: date | None
    setor: SetorResumo | None
    setor_trabalho: SetorResumo | None
    grupo: GrupoCliente | None
    orgao: Nomeado | None
    empresa_cadastro: EmpresaResumo | None
    referencias: list[Referencia]
    anotacoes: list[Anotacao]
