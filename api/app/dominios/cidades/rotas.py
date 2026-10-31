from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dominios.cidades import repositorio as repo
from app.dominios.cidades.esquemas import Cidade
from app.nucleo.contexto import Contexto, contexto

router = APIRouter(tags=["cidades"])


@router.get("/cidades", response_model=list[Cidade])
def buscar_cidades(
    ctx: Annotated[Contexto, Depends(contexto)],
    busca: str | None = None,
    uf: str | None = Query(None, pattern="^[A-Za-z]{2}$"),
    limite: int = Query(20, ge=1, le=100),
) -> list[Cidade]:
    """Municípios do IBGE. Lista de referência, aberta a quem estiver logado (sem permissão própria)."""
    return [Cidade.model_validate(c) for c in repo.buscar_cidades(ctx.db, busca, uf, limite)]
