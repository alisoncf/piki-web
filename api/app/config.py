import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
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

    # sem .env, usa um SQLite local para desenvolver sem servidor de banco
    database_url: str = "sqlite:///./piki-dev.db"
    # banco dos testes automatizados (opcional; sem ele, SQLite em memória)
    teste_database_url: str = ""
    ambiente: str = "dev"
    # chave para assinar os tokens de login; obrigatória em produção
    segredo_token: str = ""
    # validade do token de login (padrão: 10 horas, um turno)
    minutos_token: int = 600
    # consulta de CEP nas fichas de cliente e funcionário
    viacep_url: str = "https://viacep.com.br/ws/{cep}/json/"
    viacep_segundos: float = 5
    # consulta de CNPJ na BrasilAPI (pública, sem chave), para preencher a ficha do fornecedor
    brasilapi_cnpj_url: str = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    brasilapi_segundos: float = 8
    # arquivos enviados (documentos de clientes): numa pasta do servidor ou num MinIO (app/nucleo/arquivos.py)
    arquivos: Literal["pasta", "minio"] = "pasta"
    arquivos_pasta: str = str(RAIZ / "arquivos")
    minio_endereco: str = "localhost:9000"
    minio_usuario: str = ""
    minio_senha: str = ""
    minio_bucket: str = "piki"
    minio_https: bool = False
    # notas fiscais (D29): a pasta dos certificados A1 (.pfx), fora do repositório e do banco, e a chave que
    # cifra no banco a senha do certificado e o CSC da NFC-e
    certificados_pasta: str = str(RAIZ / "certificados")
    chave_segredos: str = ""
    # e-mail do sistema (D29), uma conta do Gmail com senha de app: manda o DANFE e o XML das notas
    email_servidor: str = "smtp.gmail.com"
    email_porta: int = 587
    email_usuario: str = ""
    email_senha: str = ""
    email_nome: str = "Piki"

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
