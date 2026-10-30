"""Login (decisão D7).

Fluxo de senha durante a convivência com o VB6:

1. Se o usuário já tem credencial no sistema novo e a senha dele não mudou no
   VB6 desde então (marca_legado igual), confere só o hash.
2. Senão, confere a senha no formato antigo (tab_usuarios.SENHA_USU). Se
   estiver certa, grava ou refaz o hash em web_credencial.

Assim ninguém precisa recadastrar senha, e uma troca de senha feita no VB6
continua valendo no sistema novo.
"""
from datetime import datetime
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import configuracao
from app.db import sessao
from app.legado import senha as senha_legado
from app.modelos import Credencial, Funcionario, Usuario
from app.seguranca import conferir_hash, criar_token, gerar_hash, ler_token, marca_legado

router = APIRouter(prefix="/auth", tags=["login"])

_ERRO_LOGIN = HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário ou senha incorretos")


class PedidoLogin(BaseModel):
    usuario: str = Field(min_length=1, max_length=20, description="Apelido (guerra_fun) ou código do funcionário")
    senha: str = Field(min_length=1, max_length=50)
    cod_emp: str | None = Field(default=None, pattern=r"^\d{2}$", description="Filial; padrão do .env se omitido")


class RespostaLogin(BaseModel):
    access_token: str
    token_type: str = "bearer"
    cod_fun: str
    nome: str | None
    cod_emp: str


class UsuarioAtual(BaseModel):
    cod_fun: str
    nome: str | None
    apelido: str | None
    cod_cargo: str
    cod_emp: str


def _buscar(db: Session, usuario: str) -> tuple[Usuario, Funcionario]:
    # mesmo critério do frmLogin: apelido ou código do funcionário
    linhas = db.execute(
        select(Usuario, Funcionario)
        .join(Funcionario, Funcionario.cod_fun == Usuario.cod_fun)
        .where(or_(Funcionario.apelido == usuario, Usuario.cod_fun == usuario))
    ).all()
    if not linhas:
        raise _ERRO_LOGIN
    if len(linhas) > 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Existem {len(linhas)} usuários com este nome. Entre com o código do funcionário.",
        )
    usu, fun = linhas[0]
    return usu, fun


def _conferir_senha(db: Session, usu: Usuario, senha: str) -> Credencial | None:
    """Devolve a credencial se a senha estiver certa, criando ou refazendo o hash se preciso."""
    marca = marca_legado(usu.senha)
    cred = db.get(Credencial, usu.cod_fun)
    if cred and cred.marca_legado == marca:
        return cred if conferir_hash(senha, cred.hash_senha) else None

    if not senha_legado.conferir(senha, usu.senha):
        return None
    agora = datetime.now()
    if cred is None:
        cred = Credencial(cod_fun=usu.cod_fun, criado_em=agora)
        db.add(cred)
    cred.hash_senha, cred.marca_legado, cred.atualizado_em = gerar_hash(senha), marca, agora
    return cred


@router.post("/login", response_model=RespostaLogin)
def login(pedido: PedidoLogin, db: Annotated[Session, Depends(sessao)]) -> RespostaLogin:
    usu, fun = _buscar(db, pedido.usuario.strip())
    cred = _conferir_senha(db, usu, pedido.senha)
    if cred is None:
        db.rollback()
        raise _ERRO_LOGIN
    if usu.status != "1":
        db.rollback()
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário desabilitado")

    cred.ultimo_login = datetime.now()
    db.commit()

    cod_emp = pedido.cod_emp or configuracao().cod_emp_padrao
    return RespostaLogin(access_token=criar_token(usu.cod_fun, cod_emp), cod_fun=usu.cod_fun,
                         nome=fun.nome, cod_emp=cod_emp)


_bearer = HTTPBearer(auto_error=False)


def usuario_atual(
    credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(sessao)],
) -> UsuarioAtual:
    """Dependência para proteger rotas: exige um token de login válido."""
    nao_autenticado = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Faça login", headers={"WWW-Authenticate": "Bearer"}
    )
    if credenciais is None:
        raise nao_autenticado
    try:
        dados = ler_token(credenciais.credentials)
    except jwt.InvalidTokenError:
        raise nao_autenticado
    fun = db.get(Funcionario, dados["sub"])
    usu = db.get(Usuario, dados["sub"])
    if fun is None or usu is None or usu.status != "1":
        raise nao_autenticado
    return UsuarioAtual(cod_fun=fun.cod_fun, nome=fun.nome, apelido=fun.apelido,
                        cod_cargo=fun.cod_cargo, cod_emp=dados["emp"])


@router.get("/eu", response_model=UsuarioAtual)
def eu(usuario: Annotated[UsuarioAtual, Depends(usuario_atual)]) -> UsuarioAtual:
    """Quem está logado e em qual filial."""
    return usuario
