from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dominios.consignacao import servico
from app.dominios.consignacao.esquemas import (
    LimitesDados, Representante, RepresentanteDados, RepresentanteNovo, RepresentanteResumo, SenhaDados,
)
from app.dominios.consignacao.modelos import Representante as ModeloRepresentante
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["consignação"])

Ver = Annotated[Contexto, Depends(exige("representantes.ver", "representantes.editar"))]
Editar = Annotated[Contexto, Depends(exige("representantes.editar"))]
Limites = Annotated[Contexto, Depends(exige("representantes.limites"))]

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicado: status.HTTP_409_CONFLICT,
}


def _http(ctx: Contexto, erro: servico.ErroConsignacao) -> HTTPException:
    ctx.db.rollback()
    return HTTPException(_STATUS[type(erro)], str(erro))


def _ficha(representante: ModeloRepresentante) -> Representante:
    dados = RepresentanteResumo.model_validate(representante).model_dump()
    campos = {campo: getattr(representante, campo) for campo in Representante.model_fields
              if campo not in dados and campo not in ("tem_senha", "comissoes")}
    return Representante(**dados, **campos, tem_senha=bool(representante.senha_hash),
                         comissoes=servico.comissoes(representante))


@router.get("/representantes", response_model=list[RepresentanteResumo])
def listar(ctx: Ver, busca: Annotated[str | None, Query(description="Parte do nome, o CPF ou o código")] = None,
           so_ativos: bool = False) -> list[RepresentanteResumo]:
    return [RepresentanteResumo.model_validate(r) for r in servico.listar(ctx.db, busca, so_ativos)]


@router.get("/representantes/{representante_id}", response_model=Representante)
def obter(representante_id: int, ctx: Ver) -> Representante:
    try:
        return _ficha(servico.obter(ctx.db, representante_id))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.post("/representantes", response_model=Representante, status_code=status.HTTP_201_CREATED)
def criar(dados: RepresentanteNovo, ctx: Editar) -> Representante:
    """O cliente passa a ser representante: os dados pessoais continuam na ficha do cliente."""
    try:
        return _ficha(servico.criar(ctx.db, dados.cliente_id, RepresentanteDados(**dados.model_dump(exclude={"cliente_id"}))))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.put("/representantes/{representante_id}", response_model=Representante)
def alterar(representante_id: int, dados: RepresentanteDados, ctx: Editar) -> Representante:
    try:
        return _ficha(servico.alterar(ctx.db, representante_id, dados))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.put("/representantes/{representante_id}/limites", response_model=Representante)
def alterar_limites(representante_id: int, dados: LimitesDados, ctx: Limites) -> Representante:
    """Limite, bloqueio (com o motivo), bloqueios de impressão e de devolução e comissões por tipo de cobrança."""
    try:
        return _ficha(servico.alterar_limites(ctx.db, representante_id, dados))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.put("/representantes/{representante_id}/senha", response_model=Representante)
def trocar_senha(representante_id: int, dados: SenhaDados, ctx: Editar) -> Representante:
    """A senha com que o representante confirma a transferência no balcão. Nunca volta da API."""
    try:
        return _ficha(servico.trocar_senha(ctx.db, representante_id, dados.senha))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
