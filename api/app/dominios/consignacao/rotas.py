from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.dominios.consignacao import servico
from app.dominios.consignacao.esquemas import Acerto, AcertoDados, AcertoNovo, ConfirmacaoAcerto, ItemAcertoNovo
from app.dominios.consignacao.esquemas import (
    ComprovanteComissao, PagamentoComissao, PagamentoComissaoDados, ParcelaDoAcerto, RelatorioComissoes,
)
from app.dominios.consignacao.esquemas import (
    Confirmacao, ConfirmacaoDevolucao, Devolucao, DevolucaoDados, DevolucaoNova, ItemComEle, ItemDevolucaoNovo, ItemNovo,
    LimitesDados, Posicao, QuantidadeDados, Representante, RepresentanteDados, RepresentanteNovo, RepresentanteResumo,
    SenhaDados, Transferencia, TransferenciaNova,
)
from app.dominios.consignacao.modelos import COMISSOES_ACERTO, SITUACOES_TRANSFERENCIA, ComissaoParcela
from app.dominios.consignacao.modelos import Acerto as ModeloAcerto
from app.dominios.consignacao.modelos import PagamentoComissao as ModeloPagamentoComissao
from app.dominios.consignacao.modelos import Representante as ModeloRepresentante
from app.dominios.receber.modelos import TIPOS_COBRANCA
from app.dominios.vendas.esquemas import ImpressaoCarne
from app.dominios.vendas.rotas import impressao_carne
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["consignação"])

# o balcão e o caixa do consignado escolhem o representante e veem a ficha dele
Ver = Annotated[Contexto, Depends(exige("representantes.ver", "representantes.editar", "consignacao.transferir",
                                        "consignacao.acertar", "consignacao.comissoes", "consignacao.pagar_comissao"))]
Editar = Annotated[Contexto, Depends(exige("representantes.editar"))]
Limites = Annotated[Contexto, Depends(exige("representantes.limites"))]
# o funcionário do balcão do consignado
Transferir = Annotated[Contexto, Depends(exige("consignacao.transferir"))]
# quem faz o acerto, no caixa do consignado
Acertar = Annotated[Contexto, Depends(exige("consignacao.acertar"))]
VerComissoes = Annotated[Contexto, Depends(exige("consignacao.comissoes", "consignacao.pagar_comissao"))]
PagarComissao = Annotated[Contexto, Depends(exige("consignacao.pagar_comissao"))]

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicado: status.HTTP_409_CONFLICT,
    servico.PedeAutorizacao: status.HTTP_403_FORBIDDEN,
}


def _http(ctx: Contexto, erro: servico.ErroConsignacao) -> HTTPException:
    ctx.db.rollback()
    # como no desconto da venda: a tela pede o login e a senha de quem libera e manda de novo
    cabecalhos = {"X-Pede-Autorizacao": "sim"} if isinstance(erro, servico.PedeAutorizacao) else None
    return HTTPException(_STATUS[type(erro)], str(erro), headers=cabecalhos)


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


@router.get("/representantes/{representante_id}/com-ele", response_model=list[ItemComEle])
def com_ele(representante_id: int, ctx: Ver) -> list[ItemComEle]:
    """O que está com o representante nesta loja, item de transferência a item (o mesmo produto repete se veio em
    transferências diferentes): é daqui que se escolhe o que volta na devolução e o que sai no acerto."""
    return [ItemComEle.model_validate(i) for i in servico.com_ele(ctx.db, ctx.empresa_id, representante_id)]


@router.get("/consignacao/devolucoes", response_model=list[Devolucao])
def devolucoes(ctx: Ver, representante_id: int | None = None) -> list[Devolucao]:
    return [Devolucao.model_validate(d) for d in servico.devolucoes(ctx.db, ctx.empresa_id, representante_id)]


@router.post("/consignacao/devolucoes", response_model=Devolucao)
def abrir_devolucao(dados: DevolucaoNova, ctx: Transferir) -> Devolucao:
    """Começa a devolução; se o representante já tem uma aberta nesta loja, devolve ela."""
    try:
        return Devolucao.model_validate(servico.abrir_devolucao(ctx.db, ctx.empresa_id, ctx.usuario, dados.representante_id))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.get("/consignacao/devolucoes/{devolucao_id}", response_model=Devolucao)
def obter_devolucao(devolucao_id: int, ctx: Ver) -> Devolucao:
    try:
        return Devolucao.model_validate(servico.obter_devolucao(ctx.db, ctx.empresa_id, devolucao_id))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.put("/consignacao/devolucoes/{devolucao_id}", response_model=Devolucao)
def alterar_devolucao(devolucao_id: int, dados: DevolucaoDados, ctx: Transferir) -> Devolucao:
    """Retificadora (corrige um produto transferido errado) e observação."""
    try:
        return Devolucao.model_validate(
            servico.alterar_devolucao(ctx.db, ctx.empresa_id, devolucao_id, dados.retificadora, dados.observacao))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.post("/consignacao/devolucoes/{devolucao_id}/itens", response_model=Devolucao)
def incluir_na_devolucao(devolucao_id: int, dados: ItemDevolucaoNovo, ctx: Transferir) -> Devolucao:
    try:
        return Devolucao.model_validate(servico.incluir_na_devolucao(
            ctx.db, ctx.empresa_id, devolucao_id, dados.item_transferencia_id, dados.quantidade))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.put("/consignacao/devolucoes/{devolucao_id}/itens/{item_id}", response_model=Devolucao)
def alterar_na_devolucao(devolucao_id: int, item_id: int, dados: QuantidadeDados, ctx: Transferir) -> Devolucao:
    try:
        return Devolucao.model_validate(
            servico.alterar_na_devolucao(ctx.db, ctx.empresa_id, devolucao_id, item_id, dados.quantidade))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.delete("/consignacao/devolucoes/{devolucao_id}", status_code=status.HTTP_204_NO_CONTENT)
def descartar_devolucao(devolucao_id: int, ctx: Transferir) -> Response:
    try:
        servico.descartar_devolucao(ctx.db, ctx.empresa_id, devolucao_id)
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/consignacao/devolucoes/{devolucao_id}/confirmar", response_model=Devolucao)
def confirmar_devolucao(devolucao_id: int, dados: ConfirmacaoDevolucao, ctx: Transferir) -> Devolucao:
    """O representante confirma com a senha: as peças voltam para a loja. Com a devolução dele bloqueada, 403 com o
    cabeçalho X-Pede-Autorizacao: manda de novo com a `liberacao` do gerente."""
    liberacao = dados.liberacao
    try:
        return Devolucao.model_validate(servico.confirmar_devolucao(
            ctx.db, ctx.empresa_id, ctx.usuario, ctx.permissoes, devolucao_id, dados.senha,
            liberacao.login if liberacao else None, liberacao.senha if liberacao else None))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


_NOMES_COMISSAO = {tipo: nome for tipo, (nome, _) in TIPOS_COBRANCA.items()} | {
    tipo: nome for tipo, (nome, _) in COMISSOES_ACERTO.items()}


def _acerto(ctx: Contexto, acerto: ModeloAcerto) -> Acerto:
    resposta = Acerto.model_validate(acerto)
    resposta.nome_comissao = _NOMES_COMISSAO.get(acerto.tipo_comissao, acerto.tipo_comissao)
    conta = servico.carne_do_acerto(ctx.db, acerto)
    if conta is not None:
        comissoes = {c.parcela_id: c.valor for c in ctx.db.query(ComissaoParcela).filter_by(acerto_id=acerto.id)}
        resposta.conta_id = conta.id
        resposta.carne = [ParcelaDoAcerto(id=p.id, numero=p.numero, vencimento=p.vencimento, valor=p.valor,
                                          comissao=comissoes.get(p.id, Decimal("0.00"))) for p in conta.parcelas]
    return resposta


@router.get("/consignacao/acertos", response_model=list[Acerto])
def acertos(ctx: Ver, representante_id: int | None = None) -> list[Acerto]:
    return [_acerto(ctx, a) for a in servico.acertos(ctx.db, ctx.empresa_id, representante_id)]


@router.post("/consignacao/acertos", response_model=Acerto)
def abrir_acerto(dados: AcertoNovo, ctx: Acertar) -> Acerto:
    """Começa o acerto; se o representante já tem um aberto nesta loja, devolve ele."""
    try:
        return _acerto(ctx, servico.abrir_acerto(ctx.db, ctx.empresa_id, ctx.usuario, dados.representante_id))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.get("/consignacao/acertos/{acerto_id}", response_model=Acerto)
def obter_acerto(acerto_id: int, ctx: Ver) -> Acerto:
    try:
        return _acerto(ctx, servico.obter_acerto(ctx.db, ctx.empresa_id, acerto_id))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.put("/consignacao/acertos/{acerto_id}", response_model=Acerto)
def alterar_acerto(acerto_id: int, dados: AcertoDados, ctx: Acertar) -> Acerto:
    """Para quem (o cliente do representante ou ele), queima, à vista ou a prazo, o tipo de cobrança (que dá o % da
    comissão), o valor negociado e as parcelas."""
    try:
        return _acerto(ctx, servico.alterar_acerto(ctx.db, ctx.empresa_id, acerto_id, dados))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.post("/consignacao/acertos/{acerto_id}/itens", response_model=Acerto)
def incluir_no_acerto(acerto_id: int, dados: ItemAcertoNovo, ctx: Acertar) -> Acerto:
    try:
        return _acerto(ctx, servico.incluir_no_acerto(
            ctx.db, ctx.empresa_id, acerto_id, dados.item_transferencia_id, dados.quantidade))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.put("/consignacao/acertos/{acerto_id}/itens/{item_id}", response_model=Acerto)
def alterar_no_acerto(acerto_id: int, item_id: int, dados: QuantidadeDados, ctx: Acertar) -> Acerto:
    try:
        return _acerto(ctx, servico.alterar_no_acerto(ctx.db, ctx.empresa_id, acerto_id, item_id, dados.quantidade))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.delete("/consignacao/acertos/{acerto_id}", status_code=status.HTTP_204_NO_CONTENT)
def descartar_acerto(acerto_id: int, ctx: Acertar) -> Response:
    try:
        servico.descartar_acerto(ctx.db, ctx.empresa_id, acerto_id)
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/consignacao/acertos/{acerto_id}/confirmar", response_model=Acerto)
def confirmar_acerto(acerto_id: int, dados: ConfirmacaoAcerto, ctx: Acertar) -> Acerto:
    """Fecha o acerto no caixa do consignado: as peças saem do que está com o representante, o pago entra no caixa
    e o resto vira o carnê. Passando do limite de crédito, 403 com X-Pede-Autorizacao: manda de novo com a
    `autorizacao` da gerência."""
    autorizacao = dados.autorizacao
    try:
        return _acerto(ctx, servico.confirmar_acerto(
            ctx.db, ctx.empresa_id, ctx.usuario, ctx.permissoes, acerto_id, dados.sessao_caixa_id, dados.pagamentos,
            autorizacao.login if autorizacao else None, autorizacao.senha if autorizacao else None))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.get("/consignacao/acertos/{acerto_id}/carne", response_model=ImpressaoCarne)
def carne_do_acerto(acerto_id: int, ctx: Ver) -> ImpressaoCarne:
    try:
        acerto = servico.obter_acerto(ctx.db, ctx.empresa_id, acerto_id)
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
    conta = servico.carne_do_acerto(ctx.db, acerto)
    if conta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este acerto não tem carnê")
    return impressao_carne(ctx.db, conta, f"acerto {acerto.numero}", acerto.confirmada_em)


def _pagamento_comissao(pagamento: ModeloPagamentoComissao) -> dict:
    return {"id": pagamento.id, "data_hora": pagamento.data_hora, "valor": pagamento.valor,
            "forma": pagamento.forma_pagamento.nome if pagamento.forma_pagamento else None,
            "usuario": pagamento.usuario.nome if pagamento.usuario else None, "estornado_em": pagamento.estornado_em,
            "estornado_por": pagamento.estornado_por.nome if pagamento.estornado_por else None,
            "do_vb6": pagamento.lancamento_id is None}


@router.get("/representantes/{representante_id}/comissoes", response_model=RelatorioComissoes)
def relatorio_comissoes(representante_id: int, ctx: VerComissoes, de: date | None = None, ate: date | None = None,
                        so_abertas: bool = True) -> RelatorioComissoes:
    try:
        return RelatorioComissoes(**servico.relatorio_comissoes(ctx.db, ctx.empresa_id, representante_id, de, ate, so_abertas))
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)


@router.get("/representantes/{representante_id}/comissoes/pagamentos", response_model=list[PagamentoComissao])
def pagamentos_de_comissao(representante_id: int, ctx: VerComissoes) -> list[PagamentoComissao]:
    return [PagamentoComissao(**_pagamento_comissao(p))
            for p in servico.pagamentos_de_comissao(ctx.db, ctx.empresa_id, representante_id)]


@router.post("/representantes/{representante_id}/comissoes/pagamentos", response_model=PagamentoComissao,
             status_code=status.HTTP_201_CREATED)
def pagar_comissao(representante_id: int, dados: PagamentoComissaoDados, ctx: PagarComissao) -> PagamentoComissao:
    try:
        pagamento = servico.pagar_comissao(ctx.db, ctx.empresa_id, ctx.usuario, representante_id, dados.valor,
                                           dados.forma_pagamento_id, dados.sessao_caixa_id, dados.de, dados.ate)
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
    return PagamentoComissao(**_pagamento_comissao(pagamento))


@router.get("/consignacao/comissoes/pagamentos/{pagamento_id}", response_model=ComprovanteComissao)
def comprovante_comissao(pagamento_id: int, ctx: VerComissoes) -> ComprovanteComissao:
    try:
        pagamento = servico.obter_pagamento_comissao(ctx.db, ctx.empresa_id, pagamento_id)
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
    return ComprovanteComissao(**_pagamento_comissao(pagamento),
                               representante=RepresentanteResumo.model_validate(pagamento.representante),
                               linhas=servico.linhas_do_pagamento(ctx.db, pagamento))


@router.post("/consignacao/comissoes/pagamentos/{pagamento_id}/estornar", response_model=PagamentoComissao)
def estornar_pagamento_comissao(pagamento_id: int, ctx: PagarComissao) -> PagamentoComissao:
    try:
        pagamento = servico.estornar_pagamento_comissao(ctx.db, ctx.empresa_id, ctx.usuario, pagamento_id)
    except servico.ErroConsignacao as e:
        raise _http(ctx, e)
    return PagamentoComissao(**_pagamento_comissao(pagamento))
