"""Hash de senha e tokens de login."""
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import configuracao

_hasher = PasswordHasher()
_ALGORITMO = "HS256"

# o VB6 não diferenciava maiúsculas e trocava alguns caracteres antes de
# comparar (P_AjustaTexto). Senhas importadas pelo ETL foram guardadas nesse
# formato e são conferidas da mesma forma até o usuário trocar a senha.
_TROCAS_LEGADO = str.maketrans({"'": "`", "[": "{", "]": "}", "|": "ö"})


def normalizar_legado(senha: str) -> str:
    return senha.upper().translate(_TROCAS_LEGADO)


def gerar_hash(senha: str, sem_caixa: bool = False) -> str:
    return _hasher.hash(normalizar_legado(senha) if sem_caixa else senha)


def conferir_hash(senha: str, hash_senha: str | None, sem_caixa: bool = False) -> bool:
    if not hash_senha:
        return False
    try:
        return _hasher.verify(hash_senha, normalizar_legado(senha) if sem_caixa else senha)
    except (VerificationError, InvalidHashError):
        return False


def criar_token(usuario_id: int, empresa_id: int | None) -> str:
    cfg = configuracao()
    agora = datetime.now(UTC)
    dados = {
        "sub": str(usuario_id),
        "emp": empresa_id,
        "iat": agora,
        "exp": agora + timedelta(minutes=cfg.minutos_token),
    }
    return jwt.encode(dados, cfg.segredo_token, algorithm=_ALGORITMO)


def ler_token(token: str) -> tuple[int, int | None]:
    """Devolve (usuario_id, empresa_id) ou levanta jwt.InvalidTokenError."""
    dados = jwt.decode(token, configuracao().segredo_token, algorithms=[_ALGORITMO])
    try:
        return int(dados["sub"]), dados.get("emp")
    except (KeyError, TypeError, ValueError) as e:
        raise jwt.InvalidTokenError("token malformado") from e
