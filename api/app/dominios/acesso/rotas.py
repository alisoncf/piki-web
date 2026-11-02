from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dominios.acesso import repositorio as repo
from app.dominios.acesso import servico
from app.dominios.acesso.esquemas import (
    AcessoDados,
    EmpresaResumo,
    Perfil,
    PerfilDados,
    PedidoLogin,
    PedidoSenhaProvisoria,
    PedidoTrocaEmpresa,
    PedidoTrocaSenha,
    Permissao,
    RespostaEu,
    RespostaSessao,
    UsuarioDados,
    UsuarioDetalhe,
    UsuarioNovo,
    UsuarioResumo,
)
from app.nucleo.banco import sessao
from app.nucleo.contexto import Contexto, Login, exige, login_atual
from app.nucleo.permissoes import AREAS, PERMISSOES

router = APIRouter(tags=["acesso"])

_ERROS = {
    servico.CredenciaisInvalidas: (status.HTTP_401_UNAUTHORIZED, "Usuário ou senha incorretos"),
    servico.UsuarioInativo: (status.HTTP_403_FORBIDDEN, "Usuário desativado"),
    servico.SemEmpresa: (status.HTTP_403_FORBIDDEN, "Usuário sem acesso a nenhuma empresa"),
    servico.EmpresaNaoPermitida: (status.HTTP_403_FORBIDDEN, "Sem acesso a esta empresa"),
}


# estes levam a mensagem do serviço
_STATUS = {
    servico.UsuarioBloqueado: status.HTTP_403_FORBIDDEN,
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicado: status.HTTP_409_CONFLICT,
    servico.Proibido: status.HTTP_403_FORBIDDEN,
}


def _http(erro: servico.ErroAcesso) -> HTTPException:
    if type(erro) in _STATUS:
        return HTTPException(_STATUS[type(erro)], str(erro))
    codigo, msg = _ERROS[type(erro)]
    return HTTPException(codigo, msg)


def _gestor(ctx: Contexto) -> servico.Gestor:
    return servico.Gestor(ctx.usuario, ctx.empresa_id, ctx.permissoes)


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


@router.post("/auth/senha", status_code=status.HTTP_204_NO_CONTENT)
def trocar_senha(pedido: PedidoTrocaSenha, login: Annotated[Login, Depends(login_atual)]) -> None:
    """O próprio usuário troca a senha. Com senha provisória, é a única coisa que ele consegue fazer."""
    try:
        servico.trocar_propria_senha(login.db, login.usuario, pedido.senha_atual, pedido.senha_nova)
    except servico.ErroAcesso as e:
        raise _http(e)


# ---------------------------------------------------------------- usuários


@router.get("/acesso/usuarios", response_model=list[UsuarioDetalhe])
def listar_usuarios(ctx: Annotated[Contexto, Depends(exige("acesso.usuarios"))]) -> list[UsuarioDetalhe]:
    """Usuários e seus acessos às empresas."""
    return [UsuarioDetalhe.model_validate(u, from_attributes=True) for u in repo.listar_usuarios(ctx.db)]


@router.get("/acesso/usuarios/{usuario_id}", response_model=UsuarioDetalhe)
def obter_usuario(usuario_id: int, ctx: Annotated[Contexto, Depends(exige("acesso.usuarios"))]) -> UsuarioDetalhe:
    try:
        return UsuarioDetalhe.model_validate(servico.obter_usuario(ctx.db, usuario_id), from_attributes=True)
    except servico.ErroAcesso as e:
        raise _http(e)


@router.post("/acesso/usuarios", response_model=UsuarioDetalhe, status_code=status.HTTP_201_CREATED)
def criar_usuario(dados: UsuarioNovo, ctx: Annotated[Contexto, Depends(exige("acesso.usuarios"))]) -> UsuarioDetalhe:
    """Cria com senha provisória. Quem não é administrador cria já com acesso à empresa ativa (perfil_id)."""
    try:
        return UsuarioDetalhe.model_validate(servico.criar_usuario_pela_tela(ctx.db, _gestor(ctx), dados),
                                             from_attributes=True)
    except servico.ErroAcesso as e:
        raise _http(e)


@router.put("/acesso/usuarios/{usuario_id}", response_model=UsuarioDetalhe)
def alterar_usuario(usuario_id: int, dados: UsuarioDados,
                    ctx: Annotated[Contexto, Depends(exige("acesso.usuarios"))]) -> UsuarioDetalhe:
    try:
        return UsuarioDetalhe.model_validate(servico.alterar_usuario(ctx.db, _gestor(ctx), usuario_id, dados),
                                             from_attributes=True)
    except servico.ErroAcesso as e:
        raise _http(e)


@router.put("/acesso/usuarios/{usuario_id}/senha", response_model=UsuarioDetalhe)
def definir_senha_provisoria(usuario_id: int, pedido: PedidoSenhaProvisoria,
                             ctx: Annotated[Contexto, Depends(exige("acesso.usuarios"))]) -> UsuarioDetalhe:
    """Senha provisória para quem esqueceu: também desbloqueia, e o usuário troca no próximo login."""
    try:
        return UsuarioDetalhe.model_validate(
            servico.definir_senha_provisoria(ctx.db, _gestor(ctx), usuario_id, pedido.senha), from_attributes=True)
    except servico.ErroAcesso as e:
        raise _http(e)


@router.post("/acesso/usuarios/{usuario_id}/desbloquear", response_model=UsuarioDetalhe)
def desbloquear(usuario_id: int, ctx: Annotated[Contexto, Depends(exige("acesso.usuarios"))]) -> UsuarioDetalhe:
    try:
        return UsuarioDetalhe.model_validate(servico.desbloquear(ctx.db, _gestor(ctx), usuario_id), from_attributes=True)
    except servico.ErroAcesso as e:
        raise _http(e)


@router.put("/acesso/usuarios/{usuario_id}/acessos/{empresa_id}", response_model=UsuarioDetalhe)
def salvar_acesso(usuario_id: int, empresa_id: int, dados: AcessoDados,
                  ctx: Annotated[Contexto, Depends(exige("acesso.usuarios"))]) -> UsuarioDetalhe:
    """Dá o acesso à empresa, troca o perfil nela ou desliga (ativo falso)."""
    try:
        return UsuarioDetalhe.model_validate(
            servico.salvar_acesso(ctx.db, _gestor(ctx), usuario_id, empresa_id, dados.perfil_id, dados.ativo),
            from_attributes=True)
    except servico.ErroAcesso as e:
        raise _http(e)


# ------------------------------------------------------------------ perfis


def _perfil(db, perfil) -> Perfil:
    return Perfil(id=perfil.id, nome=perfil.nome, descricao=perfil.descricao, desconto_maximo=perfil.desconto_maximo,
                  permissoes=sorted(p.codigo for p in perfil.permissoes), usuarios=repo.usos_do_perfil(db, perfil.id))


@router.get("/acesso/permissoes", response_model=list[Permissao])
def listar_permissoes(
    ctx: Annotated[Contexto, Depends(exige("acesso.perfis", "acesso.usuarios"))],
) -> list[Permissao]:
    """O catálogo de permissões, na ordem em que aparecem na tela de perfis."""
    return [Permissao(codigo=c, descricao=d, area=AREAS.get(c.split(".")[0], c.split(".")[0]))
            for c, d in PERMISSOES.items()]


@router.get("/acesso/perfis", response_model=list[Perfil])
def listar_perfis(ctx: Annotated[Contexto, Depends(exige("acesso.perfis", "acesso.usuarios"))]) -> list[Perfil]:
    return [_perfil(ctx.db, p) for p in servico.listar_perfis(ctx.db)]


@router.get("/acesso/perfis/{perfil_id}", response_model=Perfil)
def obter_perfil(perfil_id: int, ctx: Annotated[Contexto, Depends(exige("acesso.perfis"))]) -> Perfil:
    try:
        return _perfil(ctx.db, servico.obter_perfil(ctx.db, perfil_id))
    except servico.ErroAcesso as e:
        raise _http(e)


@router.post("/acesso/perfis", response_model=Perfil, status_code=status.HTTP_201_CREATED)
def criar_perfil(dados: PerfilDados, ctx: Annotated[Contexto, Depends(exige("acesso.perfis"))]) -> Perfil:
    try:
        return _perfil(ctx.db, servico.criar_perfil_pela_tela(ctx.db, _gestor(ctx), dados))
    except servico.ErroAcesso as e:
        raise _http(e)


@router.put("/acesso/perfis/{perfil_id}", response_model=Perfil)
def alterar_perfil(perfil_id: int, dados: PerfilDados,
                   ctx: Annotated[Contexto, Depends(exige("acesso.perfis"))]) -> Perfil:
    """Vale para todos os usuários com o perfil, em todas as empresas."""
    try:
        return _perfil(ctx.db, servico.alterar_perfil(ctx.db, _gestor(ctx), perfil_id, dados))
    except servico.ErroAcesso as e:
        raise _http(e)


@router.delete("/acesso/perfis/{perfil_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_perfil(perfil_id: int, ctx: Annotated[Contexto, Depends(exige("acesso.perfis"))]) -> None:
    """Só perfil sem usuários."""
    try:
        servico.excluir_perfil(ctx.db, perfil_id)
    except servico.ErroAcesso as e:
        raise _http(e)
