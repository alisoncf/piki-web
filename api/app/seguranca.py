"""Hash de senha e tokens de login."""
import hashlib
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import configuracao
from app.legado.senha import ajustar_texto

_hasher = PasswordHasher()
_ALGORITMO = "HS256"


def normalizar(senha: str) -> str:
    """A senha não diferencia maiúsculas, como no VB6: o hash é feito sobre o texto ajustado."""
    return ajustar_texto(senha)


def gerar_hash(senha: str) -> str:
    return _hasher.hash(normalizar(senha))


def conferir_hash(senha: str, hash_senha: str) -> bool:
    try:
        return _hasher.verify(hash_senha, normalizar(senha))
    except (VerifyMismatchError, InvalidHashError):
        return False


def marca_legado(senha_legado: str | None) -> str:
    """Impressão digital do SENHA_USU, para saber se a senha mudou no VB6."""
    return hashlib.sha256((senha_legado or "").rstrip().encode("utf-8")).hexdigest()


def criar_token(cod_fun: str, cod_emp: str) -> str:
    cfg = configuracao()
    agora = datetime.now(UTC)
    dados = {
        "sub": cod_fun,
        "emp": cod_emp,
        "iat": agora,
        "exp": agora + timedelta(minutes=cfg.minutos_token),
    }
    return jwt.encode(dados, cfg.segredo_token, algorithm=_ALGORITMO)


def ler_token(token: str) -> dict:
    """Devolve os dados do token ou levanta jwt.InvalidTokenError."""
    return jwt.decode(token, configuracao().segredo_token, algorithms=[_ALGORITMO])
