from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dominios.acesso import repositorio as repo
from app.dominios.acesso import servico
from app.dominios.acesso.esquemas import (
    AcessoEmpresa,
    EmpresaResumo,
    PedidoLogin,
    PedidoTrocaEmpresa,
    RespostaEu,
    RespostaSessao,
    UsuarioDetalhe,
    UsuarioResumo,
)
from app.nucleo.banco import sessao
from app.nucleo.contexto import Contexto, Login, exige, login_atual

router = APIRouter(tags=["acesso"])

_ERROS = {
    servico.CredenciaisInvalidas: (status.HTTP_401_UNAUTHORIZED, "Usuário ou senha incorretos"),
    servico.UsuarioInativo: (status.HTTP_403_FORBIDDEN, "Usuário desativado"),
    servico.SemEmpresa: (status.HTTP_403_FORBIDDEN, "Usuário sem acesso a nenhuma empresa"),
    servico.EmpresaNaoPermitida: (status.HTTP_403_FORBIDDEN, "Sem acesso a esta empresa"),
}


def _http(erro: servico.ErroAcesso) -> HTTPException:
    codigo, msg = _ERROS[type(erro)]
    return HTTPException(codigo, msg)


def _resposta(s: servico.SessaoAberta) -> RespostaSessao:
    return RespostaSessao(
        access_token=s.token,
        usuario=UsuarioResumo.model_validate(s.usuario),
        empresa=EmpresaResumo.model_validate(s.empresa) if s.empresa else None,
        empresas=[EmpresaResumo.model_validate(e) for e in s.empresas],
        ultima_empresa_id=s.usuario.ultima_empresa_id,
    )


@router.post("/auth/login", response_model=RespostaSessao)
def login(pedido: PedidoLogin, db: Annotated[Session, Depends(sessao)]) -> RespostaSessao:
    """Entra no sistema. Se o usuário tem várias empresas e nenhuma foi informada, a resposta vem sem empresa ativa."""
    try:
        return _resposta(servico.login(db, pedido.login, pedido.senha, pedido.empresa_id))
    except servico.ErroAcesso as e:
        raise _http(e)


@router.post("/auth/empresa", response_model=RespostaSessao)
def trocar_empresa(pedido: PedidoTrocaEmpresa, login: Annotated[Login, Depends(login_atual)]) -> RespostaSessao:
    """Escolhe ou troca a empresa ativa. Devolve um token novo."""
    try:
        return _resposta(servico.trocar_empresa(login.db, login.usuario, pedido.empresa_id))
    except servico.ErroAcesso as e:
        raise _http(e)


@router.get("/auth/eu", response_model=RespostaEu)
def eu(login: Annotated[Login, Depends(login_atual)]) -> RespostaEu:
    """Quem está logado, em qual empresa, e o que pode fazer nela."""
    db = login.db
    empresa = None
    permissoes: set[str] = set()
    if login.empresa_id is not None and servico.pode_acessar(db, login.usuario, login.empresa_id):
        empresa = repo.empresa_ativa(db, login.empresa_id)
        permissoes = servico.permissoes_na_empresa(db, login.usuario, login.empresa_id)
    return RespostaEu(
        usuario=UsuarioResumo.model_validate(login.usuario),
        empresa=EmpresaResumo.model_validate(empresa) if empresa else None,
        permissoes=sorted(permissoes),
        empresas=[EmpresaResumo.model_validate(e) for e in repo.empresas_do_usuario(db, login.usuario)],
    )


@router.get("/acesso/usuarios", response_model=list[UsuarioDetalhe])
def listar_usuarios(ctx: Annotated[Contexto, Depends(exige("acesso.usuarios"))]) -> list[UsuarioDetalhe]:
    """Usuários e seus acessos às empresas."""
    return [
        UsuarioDetalhe(
            id=u.id, login=u.login, nome=u.nome, administrador=u.administrador, ativo=u.ativo,
            acessos=[AcessoEmpresa(empresa=EmpresaResumo.model_validate(a.empresa), perfil=a.perfil.nome, ativo=a.ativo)
                     for a in u.acessos],
        )
        for u in repo.listar_usuarios(ctx.db)
    ]
