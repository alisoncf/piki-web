"""Segredos guardados no banco (senha do certificado, CSC da NFC-e), cifrados (D29).

A chave fica só no .env do servidor (PIKI_CHAVE_SEGREDOS): quem tiver só uma cópia
do banco não lê os segredos. Trocar a chave exige cadastrar os segredos de novo.
"""
from cryptography.fernet import Fernet, InvalidToken

from app.config import configuracao


class SemChave(Exception):
    """Falta a chave no .env, ou ela não é a que cifrou o segredo."""


def _fernet() -> Fernet:
    chave = configuracao().chave_segredos
    if not chave:
        raise SemChave("Falta a PIKI_CHAVE_SEGREDOS no .env do servidor (veja o .env.example)")
    try:
        return Fernet(chave.encode())
    except ValueError:
        raise SemChave("A PIKI_CHAVE_SEGREDOS do .env não é uma chave válida (veja o .env.example)")


def cifrar(texto: str) -> str:
    return _fernet().encrypt(texto.encode()).decode()


def decifrar(cifrado: str) -> str:
    try:
        return _fernet().decrypt(cifrado.encode()).decode()
    except InvalidToken:
        raise SemChave("O segredo foi cifrado com outra chave: cadastre-o de novo")


def nova_chave() -> str:
    return Fernet.generate_key().decode()
