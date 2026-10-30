from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# o .env fica na raiz do repositório, um nível acima de api/
RAIZ = Path(__file__).resolve().parents[2]


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PIKI_",
        env_file=RAIZ / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite://"
    cod_emp_padrao: str = Field(default="01", min_length=2, max_length=2)
    ambiente: str = "dev"


@lru_cache
def configuracao() -> Configuracao:
    return Configuracao()
