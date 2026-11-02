from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.dominios.entradas import repositorio as repo
from app.dominios.entradas import servico
from app.dominios.entradas.esquemas import Item, ItemDados, Nota, NotaResumo, PaginaNotas
from app.nucleo.arquivos import ArquivoNaoEncontrado, Armazenamento, armazenamento
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["entradas"])

Ver = Annotated[Contexto, Depends(exige("entradas.ver"))]
Lancar = Annotated[Contexto, Depends(exige("entradas.lancar"))]
Arquivos = Annotated[Armazenamento, Depends(armazenamento)]
PERMISSAO_PRECOS = "produtos.precos"

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicado: status.HTTP_409_CONFLICT,
    servico.Proibido: status.HTTP_403_FORBIDDEN,
}


def _http(erro: servico.ErroEntrada) -> HTTPException:
    # a nota repetida diz qual é, para a tela abrir a que já existe
    cabecalhos = {"X-Nota-Id": str(erro.nota_id)} if isinstance(erro, servico.Duplicado) else None
    return HTTPException(_STATUS[type(erro)], str(erro), headers=cabecalhos)


@router.get("/entradas", response_model=PaginaNotas)
def listar_notas(
    ctx: Ver,
    busca: Annotated[str | None, Query(description="Fornecedor, número ou chave da nota")] = None,
    situacao: Literal["aberta", "confirmada"] | None = None,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
) -> PaginaNotas:
    """As notas de entrada da loja ativa."""
    itens, total = repo.listar_notas(ctx.db, ctx.empresa_id, busca, situacao, limite, deslocamento)
    return PaginaNotas(itens=[NotaResumo.model_validate(n) for n in itens], total=total)


@router.post(
    "/entradas",
    response_model=Nota,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"requestBody": {"required": True, "content": {"application/xml": {}}}},
)
async def carregar_xml(pedido: Request, ctx: Lancar, arquivos: Arquivos) -> Nota:
    """O XML da NF-e vai no corpo. A nota tem que ser para a empresa ativa e fica aberta até confirmar."""
    conteudo = await pedido.body()
    try:
        nota, novo = servico.carregar_xml(ctx.db, arquivos, ctx.empresa_id, conteudo, ctx.usuario.id)
    except servico.ErroEntrada as e:
        raise _http(e)
    resposta = Nota.model_validate(nota)
    resposta.fornecedor_novo = novo
    return resposta


@router.get("/entradas/{nota_id}", response_model=Nota)
def obter_nota(nota_id: int, ctx: Ver) -> Nota:
    """A nota com os itens. Se está aberta, liga sozinho os itens cujos produtos foram cadastrados depois."""
    try:
        return Nota.model_validate(servico.obter_nota(ctx.db, ctx.empresa_id, nota_id))
    except servico.ErroEntrada as e:
        raise _http(e)


@router.put("/entradas/{nota_id}/itens/{item_id}", response_model=Item)
def alterar_item(nota_id: int, item_id: int, dados: ItemDados, ctx: Lancar) -> Item:
    """Liga o item a um produto, com a embalagem e, se for mudar, o preço de venda (pede produtos.precos)."""
    try:
        return Item.model_validate(servico.alterar_item(
            ctx.db, ctx.empresa_id, nota_id, item_id, dados, PERMISSAO_PRECOS in ctx.permissoes))
    except servico.ErroEntrada as e:
        raise _http(e)


@router.post("/entradas/{nota_id}/confirmar", response_model=Nota)
def confirmar(nota_id: int, ctx: Lancar) -> Nota:
    """Dá entrada no estoque da loja e grava o custo (e o preço novo, se houver) nos produtos."""
    try:
        return Nota.model_validate(servico.confirmar(
            ctx.db, ctx.empresa_id, nota_id, ctx.usuario.id, PERMISSAO_PRECOS in ctx.permissoes))
    except servico.ErroEntrada as e:
        raise _http(e)


@router.delete("/entradas/{nota_id}", status_code=status.HTTP_204_NO_CONTENT)
def descartar(nota_id: int, ctx: Lancar) -> None:
    """Apaga a nota ainda aberta (carregada por engano)."""
    try:
        servico.descartar(ctx.db, ctx.empresa_id, nota_id)
    except servico.ErroEntrada as e:
        raise _http(e)


@router.get("/entradas/{nota_id}/xml", response_class=Response)
def baixar_xml(nota_id: int, ctx: Ver, arquivos: Arquivos) -> Response:
    try:
        nota, conteudo = servico.ler_xml(ctx.db, arquivos, ctx.empresa_id, nota_id)
    except servico.ErroEntrada as e:
        raise _http(e)
    except ArquivoNaoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "O XML da nota não foi encontrado no armazenamento")
    return Response(conteudo, media_type="application/xml", headers={
        "Content-Disposition": f'attachment; filename="{nota.chave}.xml"'})
