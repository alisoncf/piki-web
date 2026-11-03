from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dominios.receber import servico
from app.dominios.receber.esquemas import (
    ClienteDaParcela, ContaCobranca, ContaCobrancaDados, LinhaParcela, PedidoCobranca, PaginaParcelas, ParcelaAberta, ParcelasDoCliente, PedidoPrejuizo, Recebimento,
    RecebimentoDados,
)
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["crediário"])

Operar = Annotated[Contexto, Depends(exige("caixa.operar"))]
Consultar = Annotated[Contexto, Depends(exige("receber.ver"))]
Prejuizo = Annotated[Contexto, Depends(exige("receber.prejuizo"))]
Cobranca = Annotated[Contexto, Depends(exige("receber.cobranca"))]

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
            documento=conta.documento, origem=conta.origem,
            numero=p.numero, parcelas=len(conta.parcelas), vencimento=p.vencimento, valor=p.valor, aberto=p.aberto,
            dias_atraso=dias, juros=juros, prejuizo=p.prejuizo, conta_cobranca=p.conta_cobranca.nome,
        ))
    return ParcelasDoCliente(juros_ao_mes=taxa, parcelas=resposta)


@router.post("/crediario/recebimentos", response_model=Recebimento, status_code=status.HTTP_201_CREATED)
def receber(dados: RecebimentoDados, ctx: Operar) -> Recebimento:
    """O caixa recebe parcelas (toda ou parte de cada uma, com os juros que cobrar), em uma ou mais formas."""
    try:
        recebimento = servico.receber(ctx.db, ctx.empresa_id, ctx.usuario.id, dados)
    except servico.ErroReceber as e:
        raise _http(ctx, e)
    resposta = Recebimento.model_validate(recebimento)
    resposta.quitou = servico.em_aberto(ctx.db, dados.cliente_id) == 0  # o VB6 avisa para repassar ao vendedor
    return resposta


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


@router.get("/receber/parcelas", response_model=PaginaParcelas)
def consultar(
    ctx: Consultar,
    situacao: Literal["aberto", "pagas", "todas"] = "aberto",
    loja: Annotated[int | None, Query(description="A loja que vendeu; sem ela, todas")] = None,
    cliente_id: int | None = None,
    busca: Annotated[str | None, Query(description="Nome ou CPF/CNPJ do cliente")] = None,
    documento: Annotated[str | None, Query(description="Começo do número do documento")] = None,
    origem: Literal["venda", "acerto", "avulso"] | None = None,
    historico: str | None = None,
    data: Literal["vencimento", "inicial", "emissao"] = "vencimento",
    de: date | None = None,
    ate: date | None = None,
    valor: Annotated[Decimal | None, Query(description="O que falta pagar, exato")] = None,
    cidade_id: int | None = None,
    setor_id: int | None = None,
    orgao_id: int | None = None,
    grupo_id: int | None = None,
    bloqueio: Literal["bloqueados", "liberados"] | None = None,
    credito_suspenso: bool | None = None,
    conta_cobranca_id: Annotated[int | None, Query(description="Com quem o carnê está para cobrar")] = None,
    prejuizo: Annotated[Literal["fora", "so", "junto"],
                        Query(description="As que caíram no prejuízo: fora da lista (o normal), só elas ou junto")] = "fora",
    ordem: Literal["vencimento", "cliente", "documento", "valor"] = "vencimento",
    limite: Annotated[int, Query(ge=1, le=500)] = 100,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
) -> PaginaParcelas:
    """As parcelas de todas as lojas que passam nos filtros, com as somas da consulta toda (não só da página)."""
    filtros = servico.Filtros(
        situacao=situacao, empresa_id=loja, cliente_id=cliente_id, busca=busca, documento=documento, origem=origem,
        historico=historico, data=data, de=de, ate=ate, valor=valor, cidade_id=cidade_id, setor_id=setor_id,
        orgao_id=orgao_id, grupo_id=grupo_id, bloqueio=bloqueio, credito_suspenso=credito_suspenso, prejuizo=prejuizo,
        conta_cobranca_id=conta_cobranca_id,
    )
    itens, total, soma_valor, soma_aberto = servico.consultar(ctx.db, filtros, ordem, limite, deslocamento)
    taxa = servico.juros_ao_mes(ctx.db)
    linhas = []
    for p in itens:
        conta, cliente = p.conta, p.conta.cliente
        dias, juros = servico.juros_sugerido(p.aberto, p.vencimento, taxa)
        setor = cliente.setor
        linhas.append(LinhaParcela(
            id=p.id, conta_id=conta.id, documento=conta.documento, origem=conta.origem, loja=conta.empresa,
            cliente=ClienteDaParcela(id=cliente.id, nome=cliente.nome, cpf_cnpj=cliente.cpf_cnpj,
                                     bloqueado=cliente.bloqueado, credito_suspenso=cliente.credito_suspenso),
            setor=setor.nome if setor else None,
            cidade=f"{setor.cidade.nome}/{setor.cidade.uf}" if setor and setor.cidade else None,
            historico=conta.historico, emissao=conta.criado_em.date(), numero=p.numero, parcelas=len(conta.parcelas),
            vencimento=p.vencimento, vencimento_inicial=p.vencimento_inicial, valor=p.valor, aberto=p.aberto,
            dias_atraso=dias, juros=juros, prejuizo=p.prejuizo, conta_cobranca=p.conta_cobranca.nome,
            prejuizo_em=p.prejuizo_em,
            prejuizo_por=p.prejuizo_por.nome if p.prejuizo_por else None, prejuizo_motivo=p.prejuizo_motivo,
        ))
    return PaginaParcelas(itens=linhas, total=total, soma_valor=soma_valor, soma_aberto=soma_aberto, juros_ao_mes=taxa)


@router.post("/receber/prejuizo")
def marcar_prejuizo(pedido: PedidoPrejuizo, ctx: Prejuizo) -> dict:
    """As parcelas caem no prejuízo (não se espera mais receber): saem da lista, mas o cliente continua devendo."""
    if not pedido.motivo or not pedido.motivo.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Informe por que as parcelas caíram no prejuízo")
    try:
        return {"alteradas": servico.marcar_prejuizo(ctx.db, ctx.usuario.id, pedido.parcelas, pedido.motivo.strip())}
    except servico.ErroReceber as e:
        raise _http(ctx, e)


@router.post("/receber/prejuizo/tirar")
def tirar_prejuizo(pedido: PedidoPrejuizo, ctx: Prejuizo) -> dict:
    """As parcelas voltam a ser cobradas."""
    try:
        return {"alteradas": servico.tirar_prejuizo(ctx.db, pedido.parcelas)}
    except servico.ErroReceber as e:
        raise _http(ctx, e)


@router.get("/receber/contas-cobranca", response_model=list[ContaCobranca])
def listar_contas_cobranca(ctx: Annotated[Contexto, Depends(exige("receber.ver", "receber.cobranca", "caixa.operar"))]
                           ) -> list[ContaCobranca]:
    """Onde os carnês podem estar para cobrar: a Geral (na loja) primeiro."""
    return [ContaCobranca.model_validate(c) for c in servico.listar_contas_cobranca(ctx.db)]


@router.post("/receber/contas-cobranca", response_model=ContaCobranca, status_code=status.HTTP_201_CREATED)
def criar_conta_cobranca(dados: ContaCobrancaDados, ctx: Cobranca) -> ContaCobranca:
    try:
        return ContaCobranca.model_validate(servico.salvar_conta_cobranca(ctx.db, None, dados.nome.strip(), dados.ativo))
    except servico.ErroReceber as e:
        raise _http(ctx, e)


@router.put("/receber/contas-cobranca/{conta_id}", response_model=ContaCobranca)
def alterar_conta_cobranca(conta_id: int, dados: ContaCobrancaDados, ctx: Cobranca) -> ContaCobranca:
    try:
        return ContaCobranca.model_validate(servico.salvar_conta_cobranca(ctx.db, conta_id, dados.nome.strip(), dados.ativo))
    except servico.ErroReceber as e:
        raise _http(ctx, e)


@router.post("/receber/cobranca")
def mudar_cobranca(pedido: PedidoCobranca, ctx: Cobranca) -> dict:
    """Muda as parcelas de conta de cobrança, em lote."""
    try:
        return {"alteradas": servico.mudar_cobranca(ctx.db, pedido.parcelas, pedido.conta_cobranca_id)}
    except servico.ErroReceber as e:
        raise _http(ctx, e)
