from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dominios.vendas import servico
from app.dominios.empresas.modelos import Empresa
from app.dominios.vendas.esquemas import (
    BuscaPorCpf, ClienteResumido, Consumidor,
    Carne, ClienteDoCarne, Credito, ImpressaoCarne, Item, ItemAlteracao, ItemNovo, LojaDoCarne, PaginaVendas,
    PedidoCancelamento, PedidoDesconto, PedidoForma, PedidoRecebimento, Venda, VendaDados, VendaResumo,
)
from app.dominios.vendas.modelos import ABERTA, FECHADA, SITUACOES
from app.dominios.vendas.modelos import Venda as ModeloVenda
from app.nucleo.contexto import Contexto, exige
from app.nucleo.documentos import cpf_valido, so_digitos

router = APIRouter(tags=["vendas"])

Ver = Annotated[Contexto, Depends(exige("vendas.ver", "vendas.vender", "caixa.operar"))]
Vender = Annotated[Contexto, Depends(exige("vendas.vender"))]
Receber = Annotated[Contexto, Depends(exige("caixa.operar"))]
Reabrir = Annotated[Contexto, Depends(exige("vendas.vender", "caixa.operar"))]

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.PedeAutorizacao: status.HTTP_403_FORBIDDEN,
}


def _http(ctx: Contexto, erro: servico.ErroVenda) -> HTTPException:
    ctx.db.rollback()  # nada do que foi mexido antes do erro fica valendo
    cabecalhos = {"X-Pede-Autorizacao": "sim"} if isinstance(erro, servico.PedeAutorizacao) else None
    return HTTPException(_STATUS[type(erro)], str(erro), headers=cabecalhos)


def _so_as_suas(ctx: Contexto) -> int | None:
    """O vendedor (sem vendas.ver nem caixa.operar) só vê e mexe nas vendas que ele mesmo abriu; a gerência e o
    caixa veem todas. Devolve o id do vendedor, ou None se vê todas."""
    if "vendas.ver" in ctx.permissoes or "caixa.operar" in ctx.permissoes:
        return None
    return ctx.usuario.id


def _do_vendedor(ctx: Contexto, venda_id: int) -> None:
    """A venda de outro vendedor é como se não existisse para ele."""
    dono = _so_as_suas(ctx)
    if dono is not None:
        venda = ctx.db.get(ModeloVenda, venda_id)
        if venda is None or venda.vendedor_id != dono:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Venda não encontrada")


def _venda(ctx: Contexto, venda: ModeloVenda, avisos: list[str] | None = None) -> Venda:
    resposta = Venda.model_validate(venda)
    resposta.avisos = avisos or []
    if (credito := servico.credito(ctx.db, venda)) is not None:
        resposta.credito = Credito.model_validate(credito)
    if venda.data_base is not None and (carne := servico.carne(ctx.db, venda)) is not None:
        resposta.carne = Carne.model_validate(carne)
    if venda.situacao in (ABERTA, FECHADA):
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
    """Vendas da loja, da mais nova para a mais antiga. As abertas há mais de 10 dias vencem aqui.
    O vendedor só vê as dele."""
    vendedor = _so_as_suas(ctx) or (ctx.usuario.id if minhas else None)
    itens, total = servico.listar(ctx.db, ctx.empresa_id, situacao, busca, vendedor, limite, deslocamento)
    return PaginaVendas(itens=[VendaResumo.model_validate(v) for v in itens], total=total)


@router.post("/vendas", response_model=Venda, status_code=status.HTTP_201_CREATED)
def criar(ctx: Vender) -> Venda:
    return _venda(ctx, servico.criar(ctx.db, ctx.empresa_id, ctx.usuario.id))


@router.get("/vendas/{venda_id}", response_model=Venda)
def obter(venda_id: int, ctx: Ver) -> Venda:
    try:
        _do_vendedor(ctx, venda_id)
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
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.alterar(ctx.db, ctx.empresa_id, ctx.usuario, ctx.permissoes, venda_id, dados))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/itens", response_model=Venda)
def incluir_item(venda_id: int, dados: ItemNovo, ctx: Vender) -> Venda:
    try:
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.incluir_item(ctx.db, ctx.empresa_id, ctx.usuario, venda_id, dados))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.put("/vendas/{venda_id}/itens/{item_id}", response_model=Venda)
def alterar_item(venda_id: int, item_id: int, dados: ItemAlteracao, ctx: Vender) -> Venda:
    try:
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.alterar_item(ctx.db, ctx.empresa_id, ctx.usuario, venda_id, item_id, dados))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.delete("/vendas/{venda_id}/itens/{item_id}", response_model=Venda)
def excluir_item(venda_id: int, item_id: int, ctx: Vender) -> Venda:
    try:
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.excluir_item(ctx.db, ctx.empresa_id, venda_id, item_id))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/desconto", response_model=Venda)
def dar_desconto(venda_id: int, pedido: PedidoDesconto, ctx: Vender) -> Venda:
    """Desconto no total, em % ou em reais, rateado entre os itens."""
    try:
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.dar_desconto(ctx.db, ctx.empresa_id, ctx.usuario, venda_id, pedido))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/fechar", response_model=Venda)
def fechar(venda_id: int, ctx: Vender) -> Venda:
    """O vendedor fecha a venda com o cliente; ela vai para o caixa receber."""
    try:
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.fechar(ctx.db, ctx.empresa_id, venda_id))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/reabrir", response_model=Venda)
def reabrir(venda_id: int, ctx: Reabrir) -> Venda:
    """A venda fechada volta a ser aberta, para o vendedor mudar."""
    try:
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.reabrir(ctx.db, ctx.empresa_id, venda_id))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/forma", response_model=Venda, responses={403: {"description": "Pede autorização"}})
def trocar_forma(venda_id: int, pedido: PedidoForma, ctx: Receber) -> Venda:
    """No caixa, o cliente muda a forma de pagamento (ou as parcelas) da venda fechada.
    Se o desconto da forma nova é outro, ele substitui o que a venda tinha."""
    try:
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.trocar_forma(ctx.db, ctx.empresa_id, ctx.usuario, ctx.permissoes, venda_id, pedido))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.get("/consumidores/{cpf}", response_model=BuscaPorCpf)
def buscar_cpf(cpf: str, ctx: Vender) -> BuscaPorCpf:
    """Quem tem este CPF: cliente cadastrado ou consumidor que já comprou (para preencher a venda)."""
    cpf = so_digitos(cpf)
    if not cpf_valido(cpf):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "CPF inválido")
    cliente, consumidor = servico.buscar_cpf(ctx.db, cpf)
    return BuscaPorCpf(cliente=ClienteResumido.model_validate(cliente) if cliente else None,
                       consumidor=Consumidor.model_validate(consumidor) if consumidor else None)


@router.post("/vendas/{venda_id}/descartar", response_model=Venda)
def descartar(venda_id: int, pedido: PedidoCancelamento, ctx: Vender) -> Venda:
    """A aberta ou fechada em que o cliente desistiu: fica descartada, com o motivo (não gerou nada para desfazer)."""
    try:
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.descartar(ctx.db, ctx.empresa_id, ctx.usuario.id, venda_id, pedido.motivo))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/cancelar", response_model=Venda)
def cancelar(venda_id: int, pedido: PedidoCancelamento, ctx: Annotated[Contexto, Depends(exige("vendas.cancelar"))]) -> Venda:
    """Só a venda efetivada (recebida), nos primeiros dias e sem parcela paga: desfaz o caixa, o estoque e o carnê.
    A NFC-e é cancelada pelo usuário, à parte. A aberta ou fechada é descartada, não cancelada."""
    try:
        _do_vendedor(ctx, venda_id)
        return _venda(ctx, servico.cancelar_recebida(ctx.db, ctx.empresa_id, ctx.usuario.id, venda_id,
                                                      pedido.motivo, pedido.sessao_caixa_id))
    except servico.ErroVenda as e:
        raise _http(ctx, e)


@router.post("/vendas/{venda_id}/receber", response_model=Venda, responses={403: {"description": "Pede autorização"}})
def receber(venda_id: int, pedido: PedidoRecebimento, ctx: Receber) -> Venda:
    """O caixa recebe: entra no caixa e baixa o estoque. `avisos` traz os produtos que ficaram negativos.

    O cliente pode pagar em várias formas (`pagamentos`); o troco é do dinheiro. No crediário, os
    pagamentos são a entrada e o resto vira o carnê, contado da `data_base`. Acima do limite disponível do cliente:
    403 com o cabeçalho X-Pede-Autorizacao, como no desconto.
    """
    try:
        _do_vendedor(ctx, venda_id)
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
        _do_vendedor(ctx, venda_id)
        venda = servico.obter(ctx.db, ctx.empresa_id, venda_id)
    except servico.ErroVenda as e:
        raise _http(ctx, e)
    conta = servico.carne(ctx.db, venda)
    if conta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esta venda não tem carnê")
    return impressao_carne(ctx.db, conta, f"venda {venda.numero}", venda.recebida_em, venda=venda.numero)


def impressao_carne(db, conta, documento: str, data, venda: int | None = None) -> ImpressaoCarne:
    """O carnê impresso de uma conta (da venda ou do acerto de consignação)."""
    loja = db.get(Empresa, conta.empresa_id)
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
        venda=venda,
        documento=documento,
        data=data,
        cliente=ClienteDoCarne(
            id=cliente.id, nome=cliente.nome, cpf_cnpj=cliente.cpf_cnpj,
            endereco=_juntar(_juntar(cliente.logradouro, cliente.numero and f"nº {cliente.numero}", cliente.complemento),
                             setor and _juntar(setor.tipo, setor.nome), cliente.cep and f"CEP {cliente.cep}",
                             separador=" - "),
            cidade=f"{cidade.nome}/{cidade.uf}" if cidade else "",
        ),
        carne=Carne.model_validate(conta),
    )
