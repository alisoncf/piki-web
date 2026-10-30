import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
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
    # chave para assinar os tokens de login; obrigatória em produção
    segredo_token: str = ""
    # validade do token de login (padrão: 10 horas, um turno)
    minutos_token: int = 600

    @model_validator(mode="after")
    def _segredo(self) -> "Configuracao":
        if not self.segredo_token:
            if self.ambiente == "producao":
                raise ValueError("PIKI_SEGREDO_TOKEN é obrigatório em produção")
            # em dev, gera uma chave por execução: os logins caem ao reiniciar a API
            self.segredo_token = secrets.token_urlsafe(32)
        return self


@lru_cache
def configuracao() -> Configuracao:
    return Configuracao()
