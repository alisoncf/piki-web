from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContaPlanoDados(BaseModel):
    tipo: Literal["receita", "despesa"]
    nome: str = Field(min_length=1, max_length=60)
    ativo: bool = True


class ContaPlano(ContaPlanoDados):
    model_config = ConfigDict(from_attributes=True)

    id: int
