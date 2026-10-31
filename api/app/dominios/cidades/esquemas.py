from pydantic import BaseModel, ConfigDict


class Cidade(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_ibge: str
    nome: str
    uf: str
