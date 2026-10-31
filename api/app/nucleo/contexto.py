"""Quem está fazendo a requisição e em qual empresa.

Use nas rotas:

    @router.get("/clientes")
    def listar(ctx: Annotated[Contexto, Depends(exige("clientes.ver"))]): ...

`ctx.empresa_id` é a empresa ativa; toda consulta a dado por empresa (D9)
deve filtrar por ela.
"""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.dominios.acesso import servico
from app.dominios.acesso.modelos import Usuario
from app.nucleo.banco import sessao
from app.nucleo.seguranca import ler_token

_bearer = HTTPBearer(auto_error=False)


def _nao_autenticado() -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, "Faça login", headers={"WWW-Authenticate": "Bearer"})


@dataclass
class Login:
    usuario: Usuario
    empresa_id: int | None
    db: Session


@dataclass
class Contexto:
    usuario: Usuario
    empresa_id: int
    permissoes: set[str]
    db: Session


def login_atual(
    credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(sessao)],
) -> Login:
    """Exige um token válido de um usuário ativo. A empresa pode ainda não ter sido escolhida."""
    if credenciais is None:
        raise _nao_autenticado()
    try:
        usuario_id, empresa_id = ler_token(credenciais.credentials)
    except jwt.InvalidTokenError:
        raise _nao_autenticado()
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        raise _nao_autenticado()
    return Login(usuario, empresa_id, db)


def contexto(login: Annotated[Login, Depends(login_atual)]) -> Contexto:
    """Exige login e empresa escolhida, e confere se o acesso à empresa continua valendo."""
    if login.empresa_id is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Escolha a empresa")
    if not servico.pode_acessar(login.db, login.usuario, login.empresa_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem acesso a esta empresa")
    perms = servico.permissoes_na_empresa(login.db, login.usuario, login.empresa_id)
    return Contexto(login.usuario, login.empresa_id, perms, login.db)


def exige(*permissoes: str) -> Callable[..., Contexto]:
    """Dependência que exige uma permissão na empresa ativa (com várias, basta uma delas)."""

    def _verificar(ctx: Annotated[Contexto, Depends(contexto)]) -> Contexto:
        if not any(p in ctx.permissoes for p in permissoes):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Sem permissão: {' ou '.join(permissoes)}")
        return ctx

    return _verificar
