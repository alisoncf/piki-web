from pydantic import BaseModel, ConfigDict


class Cidade(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_ibge: str
    nome: str
    uf: str


class SetorResumo(BaseModel):
    """Setor (bairro) com a sua cidade: é por ele que clientes e funcionários têm cidade."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cidade: Cidade | None
