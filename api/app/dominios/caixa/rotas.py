from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dominios.caixa import servico
from app.dominios.caixa.esquemas import (
    Caixa, CaixaDados, Forma, FormaDados, Lancamento, LancamentoDados, PaginaSessoes, PedidoAbertura,
    PedidoFechamento, Sessao, SessaoResumo, TipoDeForma, Total,
)
from app.dominios.caixa.modelos import FECHADO, TIPOS_DE_FORMA, SessaoCaixa
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["caixa"])

Operar = Annotated[Contexto, Depends(exige("caixa.operar", "caixa.conferir"))]
Configurar = Annotated[Contexto, Depends(exige("caixa.configurar"))]

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicado: status.HTTP_409_CONFLICT,
}


def _http(erro: servico.ErroCaixa) -> HTTPException:
    return HTTPException(_STATUS[type(erro)], str(erro))


def _sessao(ctx: Contexto, sessao: SessaoCaixa) -> Sessao:
    """A conferência é cega: o saldo esperado só aparece para quem confere, ou depois de fechado."""
    resposta = Sessao.model_validate(sessao)
    if sessao.situacao == FECHADO or "caixa.conferir" in ctx.permissoes:
        resposta.totais = [Total.model_validate(t, from_attributes=True) for t in servico.totais(ctx.db, sessao)]
    return resposta


@router.get("/formas-pagamento", response_model=list[Forma])
def listar_formas(
    ctx: Annotated[Contexto, Depends(exige("caixa.operar", "caixa.conferir", "caixa.configurar", "vendas.vender", "vendas.ver",
                                                   "consignacao.acertar"))],
    so_ativas: bool = False,
) -> list[Forma]:
    return [Forma.model_validate(f) for f in servico.listar_formas(ctx.db, so_ativas)]


@router.get("/formas-pagamento/tipos", response_model=list[TipoDeForma])
def tipos_de_forma(ctx: Configurar) -> list[TipoDeForma]:
    return [TipoDeForma(codigo=c, nome=n) for c, (n, _) in TIPOS_DE_FORMA.items()]


@router.post("/formas-pagamento", response_model=Forma, status_code=status.HTTP_201_CREATED)
def criar_forma(dados: FormaDados, ctx: Configurar) -> Forma:
    try:
        return Forma.model_validate(servico.criar_forma(ctx.db, dados))
    except servico.ErroCaixa as e:
        raise _http(e)


@router.put("/formas-pagamento/{forma_id}", response_model=Forma)
def alterar_forma(forma_id: int, dados: FormaDados, ctx: Configurar) -> Forma:
    try:
        return Forma.model_validate(servico.alterar_forma(ctx.db, forma_id, dados))
    except servico.ErroCaixa as e:
        raise _http(e)


@router.get("/caixas", response_model=list[Caixa])
def listar_caixas(ctx: Annotated[Contexto, Depends(exige("caixa.operar", "caixa.conferir", "caixa.configurar",
                                                         "consignacao.acertar"))]) -> list[Caixa]:
    """Os caixas da loja ativa, com a sessão aberta de cada um."""
    resposta = []
    for caixa, sessao in servico.listar_caixas(ctx.db, ctx.empresa_id):
        item = Caixa.model_validate(caixa)
        item.sessao = SessaoResumo.model_validate(sessao) if sessao else None
        resposta.append(item)
    return resposta


@router.post("/caixas", response_model=Caixa, status_code=status.HTTP_201_CREATED)
def criar_caixa(dados: CaixaDados, ctx: Configurar) -> Caixa:
    try:
        return Caixa.model_validate(servico.criar_caixa(ctx.db, ctx.empresa_id, dados))
    except servico.ErroCaixa as e:
        raise _http(e)


@router.put("/caixas/{caixa_id}", response_model=Caixa)
def alterar_caixa(caixa_id: int, dados: CaixaDados, ctx: Configurar) -> Caixa:
    try:
        return Caixa.model_validate(servico.alterar_caixa(ctx.db, ctx.empresa_id, caixa_id, dados))
    except servico.ErroCaixa as e:
        raise _http(e)


@router.post("/caixas/{caixa_id}/abrir", response_model=Sessao, status_code=status.HTTP_201_CREATED)
def abrir(caixa_id: int, pedido: PedidoAbertura, ctx: Operar) -> Sessao:
    try:
        return _sessao(ctx, servico.abrir(ctx.db, ctx.empresa_id, caixa_id, pedido.fundo, ctx.usuario.id))
    except servico.ErroCaixa as e:
        raise _http(e)


@router.get("/caixas/{caixa_id}/sessoes", response_model=PaginaSessoes)
def listar_sessoes(
    caixa_id: int, ctx: Annotated[Contexto, Depends(exige("caixa.conferir"))],
    limite: Annotated[int, Query(ge=1, le=200)] = 20,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
) -> PaginaSessoes:
    """Os fechamentos do caixa, do mais novo para o mais antigo."""
    try:
        itens, total = servico.listar_sessoes(ctx.db, ctx.empresa_id, caixa_id, limite, deslocamento)
    except servico.ErroCaixa as e:
        raise _http(e)
    return PaginaSessoes(itens=[SessaoResumo.model_validate(s) for s in itens], total=total)


@router.get("/caixas/sessoes/{sessao_id}", response_model=Sessao)
def obter_sessao(sessao_id: int, ctx: Operar) -> Sessao:
    try:
        return _sessao(ctx, servico.obter_sessao(ctx.db, ctx.empresa_id, sessao_id))
    except servico.ErroCaixa as e:
        raise _http(e)


@router.post("/caixas/sessoes/{sessao_id}/lancamentos", response_model=Lancamento, status_code=status.HTTP_201_CREATED)
def lancar(sessao_id: int, dados: LancamentoDados, ctx: Operar) -> Lancamento:
    """Entrada ou saída avulsa: troco, despesa, vale, comissão de cobrador..."""
    try:
        return Lancamento.model_validate(servico.lancar(ctx.db, ctx.empresa_id, sessao_id, dados, ctx.usuario.id))
    except servico.ErroCaixa as e:
        raise _http(e)


@router.post("/caixas/sessoes/{sessao_id}/lancamentos/{lancamento_id}/estornar", response_model=Lancamento)
def estornar(sessao_id: int, lancamento_id: int, ctx: Operar) -> Lancamento:
    try:
        return Lancamento.model_validate(
            servico.estornar(ctx.db, ctx.empresa_id, sessao_id, lancamento_id, ctx.usuario.id))
    except servico.ErroCaixa as e:
        raise _http(e)


@router.post("/caixas/sessoes/{sessao_id}/fechar", response_model=Sessao)
def fechar(sessao_id: int, pedido: PedidoFechamento, ctx: Operar) -> Sessao:
    """Quem fecha informa o que contou; a resposta já traz a diferença de cada forma."""
    try:
        return _sessao(ctx, servico.fechar(ctx.db, ctx.empresa_id, sessao_id, pedido, ctx.usuario.id))
    except servico.ErroCaixa as e:
        raise _http(e)
