from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dominios.receber import servico
from app.dominios.receber.esquemas import ParcelaAberta, ParcelasDoCliente, Recebimento, RecebimentoDados
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["crediário"])

Operar = Annotated[Contexto, Depends(exige("caixa.operar"))]

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def _http(ctx: Contexto, erro: servico.ErroReceber) -> HTTPException:
    ctx.db.rollback()  # nada do que foi mexido antes do erro fica valendo
    return HTTPException(_STATUS[type(erro)], str(erro))


@router.get("/crediario/clientes/{cliente_id}/parcelas", response_model=ParcelasDoCliente)
def parcelas(cliente_id: int, ctx: Operar) -> ParcelasDoCliente:
    """O que o cliente tem para pagar, em todas as lojas, com os juros de atraso sugeridos para hoje."""
    try:
        abertas = servico.parcelas_abertas(ctx.db, cliente_id)
    except servico.ErroReceber as e:
        raise _http(ctx, e)
    taxa = servico.juros_ao_mes(ctx.db)
    resposta = []
    for p in abertas:
        dias, juros = servico.juros_sugerido(p.aberto, p.vencimento, taxa)
        conta = p.conta
        resposta.append(ParcelaAberta(
            id=p.id, conta_id=conta.id, loja=conta.empresa, venda=conta.venda.numero if conta.venda else None,
            numero=p.numero, parcelas=len(conta.parcelas), vencimento=p.vencimento, valor=p.valor, aberto=p.aberto,
            dias_atraso=dias, juros=juros,
        ))
    return ParcelasDoCliente(juros_ao_mes=taxa, parcelas=resposta)


@router.post("/crediario/recebimentos", response_model=Recebimento, status_code=status.HTTP_201_CREATED)
def receber(dados: RecebimentoDados, ctx: Operar) -> Recebimento:
    """O caixa recebe parcelas (toda ou parte de cada uma, com os juros que cobrar), em uma ou mais formas."""
    try:
        return Recebimento.model_validate(servico.receber(ctx.db, ctx.empresa_id, ctx.usuario.id, dados))
    except servico.ErroReceber as e:
        raise _http(ctx, e)


@router.get("/crediario/recebimentos/{recebimento_id}", response_model=Recebimento)
def obter(recebimento_id: int, ctx: Operar) -> Recebimento:
    try:
        return Recebimento.model_validate(servico.obter(ctx.db, ctx.empresa_id, recebimento_id))
    except servico.ErroReceber as e:
        raise _http(ctx, e)


@router.post("/crediario/recebimentos/{recebimento_id}/estornar", response_model=Recebimento)
def estornar(recebimento_id: int, ctx: Operar) -> Recebimento:
    """Recebimento errado: as parcelas voltam a dever e os lançamentos saem do caixa (com o caixa ainda aberto)."""
    try:
        return Recebimento.model_validate(servico.estornar(ctx.db, ctx.empresa_id, ctx.usuario.id, recebimento_id))
    except servico.ErroReceber as e:
        raise _http(ctx, e)
