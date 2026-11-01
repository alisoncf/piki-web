from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.dominios.empresas import repositorio as repo
from app.dominios.empresas import servico
from app.dominios.empresas.esquemas import Empresa, EmpresaDados, EmpresaNova
from app.nucleo.contexto import Contexto, contexto, exige

router = APIRouter(tags=["empresas"])

_STATUS = {
    servico.NaoEncontrada: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicada: status.HTTP_409_CONFLICT,
}

Gerenciar = Annotated[Contexto, Depends(exige("acesso.empresas"))]


def _http(erro: servico.ErroEmpresa) -> HTTPException:
    return HTTPException(_STATUS[type(erro)], str(erro))


@router.get("/empresas", response_model=list[Empresa])
def listar_empresas(ctx: Gerenciar) -> list[Empresa]:
    """Todas as empresas do grupo, ativas ou não."""
    return [Empresa.model_validate(e) for e in repo.listar_empresas(ctx.db)]


@router.get("/empresas/{empresa_id}", response_model=Empresa)
def obter_empresa(empresa_id: int, ctx: Gerenciar) -> Empresa:
    try:
        return Empresa.model_validate(servico.obter_empresa(ctx.db, empresa_id))
    except servico.ErroEmpresa as e:
        raise _http(e)


@router.post("/empresas", response_model=Empresa, status_code=status.HTTP_201_CREATED)
def criar_empresa(dados: EmpresaNova, ctx: Gerenciar) -> Empresa:
    try:
        return Empresa.model_validate(servico.criar_empresa(ctx.db, dados))
    except servico.ErroEmpresa as e:
        raise _http(e)


@router.put("/empresas/{empresa_id}", response_model=Empresa)
def alterar_empresa(empresa_id: int, dados: EmpresaDados, ctx: Gerenciar) -> Empresa:
    """Altera a ficha. O código da empresa não muda: o ETL usa para saber de onde veio cada dado."""
    try:
        return Empresa.model_validate(servico.alterar_empresa(ctx.db, empresa_id, dados))
    except servico.ErroEmpresa as e:
        raise _http(e)


@router.get("/empresas/{empresa_id}/imagens/{tipo}", response_class=Response)
def obter_imagem(empresa_id: int, tipo: str, ctx: Annotated[Contexto, Depends(contexto)]) -> Response:
    """Logo ou QR code, para os relatórios e boletos de qualquer tela (basta estar logado)."""
    try:
        imagem = servico.obter_imagem(ctx.db, empresa_id, tipo)
    except servico.ErroEmpresa as e:
        raise _http(e)
    return Response(imagem.conteudo, media_type=imagem.tipo_conteudo, headers={"Cache-Control": "no-cache"})


@router.put(
    "/empresas/{empresa_id}/imagens/{tipo}",
    response_model=Empresa,
    openapi_extra={"requestBody": {"required": True, "content": {"image/png": {}, "image/jpeg": {}}}},
)
async def gravar_imagem(empresa_id: int, tipo: str, pedido: Request, ctx: Gerenciar) -> Empresa:
    """O arquivo PNG ou JPEG vai no corpo, sem formulário (até 1 MB). Substitui a imagem anterior."""
    conteudo = await pedido.body()
    try:
        return Empresa.model_validate(servico.gravar_imagem(ctx.db, empresa_id, tipo, conteudo))
    except servico.ErroEmpresa as e:
        raise _http(e)


@router.delete("/empresas/{empresa_id}/imagens/{tipo}", response_model=Empresa)
def apagar_imagem(empresa_id: int, tipo: str, ctx: Gerenciar) -> Empresa:
    try:
        return Empresa.model_validate(servico.apagar_imagem(ctx.db, empresa_id, tipo))
    except servico.ErroEmpresa as e:
        raise _http(e)
