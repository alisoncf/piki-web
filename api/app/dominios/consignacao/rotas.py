from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.dominios.consignacao import servico
from app.dominios.consignacao.esquemas import (
    Confirmacao, ItemNovo, LimitesDados, Posicao, QuantidadeDados, Representante, RepresentanteDados,
    RepresentanteNovo, RepresentanteResumo, SenhaDados, Transferencia, TransferenciaNova,
)
from app.dominios.consignacao.modelos import SITUACOES_TRANSFERENCIA
from app.dominios.consignacao.modelos import Representante as ModeloRepresentante
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["consignação"])

# o balcão do consignado escolhe o representante e vê a ficha dele
Ver = Annotated[Contexto, Depends(exige("representantes.ver", "representantes.editar", "consignacao.transferir"))]
Editar = Annotated[Contexto, Depends(exige("representantes.editar"))]
Limites = Annotated[Contexto, Depends(exige("representantes.limites"))]
# o funcionário do balcão do consignado
Transferir = Annotated[Contexto, Depends(exige("consignacao.transferir"))]

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


@router.get("/representantes/{representante_id}/posicao", response_model=Posicao)
def posicao(representante_id: int, ctx: Ver) -> Posicao:
    """O que está com o representante nesta loja, por produto, e quanto do limite ainda tem."""
    try:
        representante = servico.obter(ctx.db, representante_id)
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
    return Posicao(**servico.posicao(ctx.db, ctx.empresa_id, representante))


@router.get("/consignacao/transferencias", response_model=list[Transferencia])
def transferencias(ctx: Ver, representante_id: int | None = None, situacao: str | None = None) -> list[Transferencia]:
    if situacao and situacao not in SITUACOES_TRANSFERENCIA:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Situação desconhecida")
    return [Transferencia.model_validate(t)
            for t in servico.transferencias(ctx.db, ctx.empresa_id, representante_id, situacao)]


@router.post("/consignacao/transferencias", response_model=Transferencia)
def abrir_transferencia(dados: TransferenciaNova, ctx: Transferir) -> Transferencia:
    """Começa a transferência; se o representante já tem uma aberta nesta loja, devolve ela."""
    try:
        return Transferencia.model_validate(
            servico.abrir_transferencia(ctx.db, ctx.empresa_id, ctx.usuario, dados.representante_id))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.get("/consignacao/transferencias/{transferencia_id}", response_model=Transferencia)
def obter_transferencia(transferencia_id: int, ctx: Ver) -> Transferencia:
    try:
        return Transferencia.model_validate(servico.obter_transferencia(ctx.db, ctx.empresa_id, transferencia_id))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.post("/consignacao/transferencias/{transferencia_id}/itens", response_model=Transferencia)
def incluir_item(transferencia_id: int, dados: ItemNovo, ctx: Transferir) -> Transferencia:
    """O produto sai pelo preço de venda do dia; o mesmo produto de novo soma na linha."""
    try:
        return Transferencia.model_validate(
            servico.incluir_item(ctx.db, ctx.empresa_id, transferencia_id, dados.produto_id, dados.quantidade))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.put("/consignacao/transferencias/{transferencia_id}/itens/{item_id}", response_model=Transferencia)
def alterar_item(transferencia_id: int, item_id: int, dados: QuantidadeDados, ctx: Transferir) -> Transferencia:
    try:
        return Transferencia.model_validate(
            servico.alterar_item(ctx.db, ctx.empresa_id, transferencia_id, item_id, dados.quantidade))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.delete("/consignacao/transferencias/{transferencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def descartar_transferencia(transferencia_id: int, ctx: Transferir) -> Response:
    """A aberta, que não mexeu em nada, some."""
    try:
        servico.descartar_transferencia(ctx.db, ctx.empresa_id, transferencia_id)
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/consignacao/transferencias/{transferencia_id}/confirmar", response_model=Transferencia)
def confirmar(transferencia_id: int, dados: Confirmacao, ctx: Transferir) -> Transferencia:
    """O representante confirma com a senha: os produtos passam ao estoque dele. Bloqueado ou passando do limite,
    422. `avisos` traz os produtos com o disponível da loja negativo."""
    try:
        transferencia, avisos = servico.confirmar(ctx.db, ctx.empresa_id, ctx.usuario, transferencia_id, dados.senha)
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
    return Transferencia.model_validate(transferencia).model_copy(update={"avisos": avisos})

