from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dominios.estoque import servico
from app.dominios.estoque.esquemas import Estoque, EstoqueDados, Movimento, PaginaMovimentos, PedidoAjuste
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["estoque"])

Ver = Annotated[Contexto, Depends(exige("estoque.ver"))]

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def _http(erro: servico.ErroEstoque) -> HTTPException:
    return HTTPException(_STATUS[type(erro)], str(erro))


@router.get("/produtos/{produto_id}/estoque", response_model=Estoque)
def obter_estoque(produto_id: int, ctx: Ver) -> Estoque:
    """O produto na loja ativa: saldo, reservado, localização e impostos."""
    try:
        return Estoque.model_validate(servico.obter_estoque(ctx.db, ctx.empresa_id, produto_id))
    except servico.ErroEstoque as e:
        raise _http(e)


@router.put("/produtos/{produto_id}/estoque", response_model=Estoque)
def alterar_estoque(produto_id: int, dados: EstoqueDados,
                    ctx: Annotated[Contexto, Depends(exige("estoque.editar"))]) -> Estoque:
    """Localização e impostos do produto na loja ativa. A quantidade só muda por movimento."""
    try:
        return Estoque.model_validate(servico.alterar_dados(ctx.db, ctx.empresa_id, produto_id, dados))
    except servico.ErroEstoque as e:
        raise _http(e)


@router.post("/produtos/{produto_id}/estoque/ajuste", response_model=Estoque)
def ajustar_estoque(produto_id: int, pedido: PedidoAjuste,
                    ctx: Annotated[Contexto, Depends(exige("estoque.ajustar"))]) -> Estoque:
    """Acerta a quantidade da loja ativa para a informada, com o motivo. Negativo é aceito."""
    try:
        return Estoque.model_validate(
            servico.ajustar(ctx.db, ctx.empresa_id, produto_id, pedido.quantidade, pedido.motivo, ctx.usuario.id))
    except servico.ErroEstoque as e:
        raise _http(e)


@router.get("/produtos/{produto_id}/estoque/movimentos", response_model=PaginaMovimentos)
def listar_movimentos(
    produto_id: int, ctx: Ver,
    limite: Annotated[int, Query(ge=1, le=200)] = 20,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
) -> PaginaMovimentos:
    """O histórico do produto na loja ativa, do mais novo para o mais antigo."""
    try:
        itens, total = servico.listar_movimentos(ctx.db, ctx.empresa_id, produto_id, limite, deslocamento)
    except servico.ErroEstoque as e:
        raise _http(e)
    return PaginaMovimentos(itens=[Movimento.model_validate(m) for m in itens], total=total)
