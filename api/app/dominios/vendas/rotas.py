from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dominios.vendas import servico
from app.dominios.empresas.modelos import Empresa
from app.dominios.vendas.esquemas import (
    Carne, ClienteDoCarne, Credito, ImpressaoCarne, Item, ItemAlteracao, ItemNovo, LojaDoCarne, PaginaVendas,
    PedidoCancelamento, PedidoDesconto, PedidoRecebimento, Venda, VendaDados, VendaResumo,
)
from app.dominios.vendas.modelos import ABERTA, SITUACOES
from app.dominios.vendas.modelos import Venda as ModeloVenda
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["vendas"])

Ver = Annotated[Contexto, Depends(exige("vendas.ver", "vendas.vender", "caixa.operar"))]
Vender = Annotated[Contexto, Depends(exige("vendas.vender"))]
Receber = Annotated[Contexto, Depends(exige("caixa.operar"))]

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.PedeAutorizacao: status.HTTP_403_FORBIDDEN,
}


def _http(ctx: Contexto, erro: servico.ErroVenda) -> HTTPException:
    ctx.db.rollback()  # nada do que foi mexido antes do erro fica valendo
    cabecalhos = {"X-Pede-Autorizacao": "sim"} if isinstance(erro, servico.PedeAutorizacao) else None
    return HTTPException(_STATUS[type(erro)], str(erro), headers=cabecalhos)


def _venda(ctx: Contexto, venda: ModeloVenda, avisos: list[str] | None = None) -> Venda:
    resposta = Venda.model_validate(venda)
    resposta.avisos = avisos or []
    if (credito := servico.credito(ctx.db, venda)) is not None:
        resposta.credito = Credito.model_validate(credito)
    if venda.entrada is not None and (carne := servico.carne(ctx.db, venda)) is not None:
        resposta.carne = Carne.model_validate(carne)
    if venda.situacao == ABERTA:
        saldos = servico.disponiveis(ctx.db, venda)
        resposta.itens = [Item.model_validate(i).model_copy(update={"disponivel": saldos.get(i.produto_id, Decimal("0.000"))})
                          for i in venda.itens]
    return resposta


@router.get("/vendas", response_model=PaginaVendas)
def listar(
    ctx: Ver,
    situacao: Annotated[str | None, Query(description=", ".join(SITUACOES))] = None,
    busca: Annotated[str | None, Query(description="Número da venda ou parte do nome do cliente")] = None,
    minhas: Annotated[bool, Query(description="Só as que eu montei")] = False,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
) -> PaginaVendas:
    """Vendas da loja, da mais nova para a mais antiga. As abertas há mais de 10 dias vencem aqui."""
    itens, total = servico.listar(ctx.db, ctx.empresa_id, situacao, busca, ctx.usuario.id if minhas else None,
                                  limite, deslocamento)
    return PaginaVendas(itens=[VendaResumo.model_validate(v) for v in itens], total=total)


@router.post("/vendas", response_model=Venda, status_code=status.HTTP_201_CREATED)
def criar(ctx: Vender) -> Venda:
    return _venda(ctx, servico.criar(ctx.db, ctx.empresa_id, ctx.usuario.id))


@router.get("/vendas/{venda_id}", response_model=Venda)
def obter(venda_id: int, ctx: Ver) -> Venda:
    try:
        return _venda(ctx, servico.obter(ctx.db, ctx.empresa_id, venda_id))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.put("/vendas/{venda_id}", response_model=Venda, responses={403: {"description": "Pede autorização"}})
def alterar(venda_id: int, dados: VendaDados, ctx: Vender) -> Venda:
    """Cliente, forma de pagamento, parcelas e observação.

    Passou do limite (desconto ou parcelas): 403 com o cabeçalho X-Pede-Autorizacao;
    mande de novo com `autorizacao` (login e senha de quem autoriza).
    """
    try:
        return _venda(ctx, servico.alterar(ctx.db, ctx.empresa_id, ctx.usuario, ctx.permissoes, venda_id, dados))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/itens", response_model=Venda)
def incluir_item(venda_id: int, dados: ItemNovo, ctx: Vender) -> Venda:
    try:
        return _venda(ctx, servico.incluir_item(ctx.db, ctx.empresa_id, ctx.usuario, venda_id, dados))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.put("/vendas/{venda_id}/itens/{item_id}", response_model=Venda)
def alterar_item(venda_id: int, item_id: int, dados: ItemAlteracao, ctx: Vender) -> Venda:
    try:
        return _venda(ctx, servico.alterar_item(ctx.db, ctx.empresa_id, ctx.usuario, venda_id, item_id, dados))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.delete("/vendas/{venda_id}/itens/{item_id}", response_model=Venda)
def excluir_item(venda_id: int, item_id: int, ctx: Vender) -> Venda:
    try:
        return _venda(ctx, servico.excluir_item(ctx.db, ctx.empresa_id, venda_id, item_id))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/desconto", response_model=Venda)
def dar_desconto(venda_id: int, pedido: PedidoDesconto, ctx: Vender) -> Venda:
    """Desconto no total, em % ou em reais, rateado entre os itens."""
    try:
        return _venda(ctx, servico.dar_desconto(ctx.db, ctx.empresa_id, ctx.usuario, venda_id, pedido))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/cancelar", response_model=Venda)
def cancelar(venda_id: int, pedido: PedidoCancelamento, ctx: Vender) -> Venda:
    try:
        return _venda(ctx, servico.cancelar(ctx.db, ctx.empresa_id, ctx.usuario.id, venda_id, pedido.motivo))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/receber", response_model=Venda, responses={403: {"description": "Pede autorização"}})
def receber(venda_id: int, pedido: PedidoRecebimento, ctx: Receber) -> Venda:
    """O caixa recebe: entra no caixa e baixa o estoque. `avisos` traz os produtos que ficaram negativos.

    No crediário, o que não foi pago na entrada vira o carnê. Acima do limite disponível do cliente:
    403 com o cabeçalho X-Pede-Autorizacao, como no desconto.
    """
    try:
        venda, avisos = servico.receber(ctx.db, ctx.empresa_id, ctx.usuario, ctx.permissoes, venda_id, pedido)
    except servico.ErroVenda as e:
        raise _http(ctx, e)
    return _venda(ctx, venda, avisos)


def _juntar(*partes: str | None, separador: str = " ") -> str:
    return separador.join(p.strip() for p in partes if p and p.strip())


@router.get("/vendas/{venda_id}/carne", response_model=ImpressaoCarne)
def carne(venda_id: int, ctx: Ver) -> ImpressaoCarne:
    """O que vai no carnê impresso da venda no crediário."""
    try:
        venda = servico.obter(ctx.db, ctx.empresa_id, venda_id)
    except servico.ErroVenda as e:
        raise _http(ctx, e)
    conta = servico.carne(ctx.db, venda)
    if conta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esta venda não tem carnê")
    loja = ctx.db.get(Empresa, venda.empresa_id)
    cidade_loja = f"{loja.cidade.nome}/{loja.cidade.uf}" if loja.cidade else None
    cliente = conta.cliente
    setor = cliente.setor
    cidade = setor.cidade if setor else None
    return ImpressaoCarne(
        loja=LojaDoCarne(
            nome=loja.nome_fantasia or loja.nome, cnpj=loja.cnpj, telefone=loja.telefone,
            endereco=_juntar(_juntar(loja.logradouro, loja.numero, loja.complemento, separador=", "),
                             loja.bairro, cidade_loja, separador=" - "),
        ),
        venda=venda.numero,
        data=venda.recebida_em,
        cliente=ClienteDoCarne(
            id=cliente.id, nome=cliente.nome, cpf_cnpj=cliente.cpf_cnpj,
            endereco=_juntar(_juntar(cliente.logradouro, cliente.numero and f"nº {cliente.numero}", cliente.complemento),
                             setor and _juntar(setor.tipo, setor.nome), cliente.cep and f"CEP {cliente.cep}",
                             separador=" - "),
            cidade=f"{cidade.nome}/{cidade.uf}" if cidade else "",
        ),
        carne=Carne.model_validate(conta),
    )
