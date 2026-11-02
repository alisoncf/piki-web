from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.dominios.estoque import repositorio as estoque
from app.dominios.produtos import repositorio as repo
from app.dominios.produtos import servico
from app.dominios.produtos.esquemas import (
    Foto, Marca, NomeDados, PaginaProdutos, Produto, ProdutoDados, ProdutoResumo, Secao, Subsecao, SubsecaoDados,
)
from app.nucleo.arquivos import ArquivoNaoEncontrado, Armazenamento, armazenamento
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["produtos"])

Ver = Annotated[Contexto, Depends(exige("produtos.ver"))]
Editar = Annotated[Contexto, Depends(exige("produtos.editar"))]
Arquivos = Annotated[Armazenamento, Depends(armazenamento)]

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicado: status.HTTP_409_CONFLICT,
    servico.Proibido: status.HTTP_403_FORBIDDEN,
}


def _http(erro: servico.ErroProduto) -> HTTPException:
    return HTTPException(_STATUS[type(erro)], str(erro))


@router.get("/produtos", response_model=PaginaProdutos)
def listar_produtos(
    ctx: Ver,
    busca: Annotated[str | None, Query(description="Código, código de barras, código do fornecedor ou palavras do nome")] = None,
    secao_id: int | None = None,
    subsecao_id: int | None = None,
    marca_id: int | None = None,
    fornecedor_id: int | None = None,
    ativo: bool | None = None,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    deslocamento: Annotated[int, Query(ge=0)] = 0,
) -> PaginaProdutos:
    """Produtos (cadastro único de todas as lojas), uma página por vez."""
    itens, total = repo.listar_produtos(ctx.db, busca, secao_id, subsecao_id, marca_id, fornecedor_id, ativo,
                                        limite, deslocamento)
    resumos = [ProdutoResumo.model_validate(p) for p in itens]
    if "estoque.ver" in ctx.permissoes:
        saldos = estoque.quantidades(ctx.db, ctx.empresa_id, [p.id for p in itens])
        for resumo in resumos:
            resumo.estoque = saldos.get(resumo.id, Decimal("0.000"))
    return PaginaProdutos(itens=resumos, total=total)


@router.get("/produtos/{produto_id}", response_model=Produto)
def obter_produto(produto_id: int, ctx: Ver) -> Produto:
    try:
        return Produto.model_validate(servico.obter_produto(ctx.db, produto_id))
    except servico.ErroProduto as e:
        raise _http(e)


@router.post("/produtos", response_model=Produto, status_code=status.HTTP_201_CREATED)
def criar_produto(dados: ProdutoDados, ctx: Editar) -> Produto:
    """O código é dado pelo sistema. Custo, margem e preços pedem produtos.precos."""
    try:
        produto = servico.criar_produto(ctx.db, dados, servico.PERMISSAO_PRECOS in ctx.permissoes)
    except servico.ErroProduto as e:
        raise _http(e)
    return Produto.model_validate(produto)


@router.put("/produtos/{produto_id}", response_model=Produto)
def alterar_produto(produto_id: int, dados: ProdutoDados, ctx: Editar) -> Produto:
    """Os códigos de barras e fornecedores enviados substituem os que existiam. Mudar custo ou preço pede produtos.precos."""
    try:
        produto = servico.alterar_produto(ctx.db, produto_id, dados, servico.PERMISSAO_PRECOS in ctx.permissoes)
    except servico.ErroProduto as e:
        raise _http(e)
    return Produto.model_validate(produto)


@router.post(
    "/produtos/{produto_id}/fotos",
    response_model=Foto,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"requestBody": {"required": True, "content": {"image/jpeg": {}, "image/png": {}}}},
)
async def enviar_foto(produto_id: int, pedido: Request, ctx: Editar, arquivos: Arquivos) -> Foto:
    """A foto (JPEG ou PNG, até 5 MB) vai no corpo, sem formulário. Entra no fim; a primeira é a principal."""
    conteudo = await pedido.body()
    try:
        return Foto.model_validate(servico.enviar_foto(ctx.db, arquivos, produto_id, conteudo, ctx.usuario.id))
    except servico.ErroProduto as e:
        raise _http(e)


@router.get("/produtos/{produto_id}/fotos/{foto_id}/arquivo", response_class=Response)
def baixar_foto(produto_id: int, foto_id: int, ctx: Ver, arquivos: Arquivos) -> Response:
    try:
        foto, conteudo = servico.ler_foto(ctx.db, arquivos, produto_id, foto_id)
    except servico.ErroProduto as e:
        raise _http(e)
    except ArquivoNaoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "O arquivo da foto não foi encontrado no armazenamento")
    # a foto de um id nunca muda: o navegador pode guardar
    return Response(conteudo, media_type=foto.tipo_conteudo, headers={
        "Cache-Control": "private, max-age=604800, immutable",
        "X-Content-Type-Options": "nosniff",
    })


@router.post("/produtos/{produto_id}/fotos/{foto_id}/principal", response_model=list[Foto])
def tornar_principal(produto_id: int, foto_id: int, ctx: Editar) -> list[Foto]:
    """Põe a foto em primeiro lugar. Devolve as fotos na ordem nova."""
    try:
        return [Foto.model_validate(f) for f in servico.tornar_principal(ctx.db, produto_id, foto_id).fotos]
    except servico.ErroProduto as e:
        raise _http(e)


@router.delete("/produtos/{produto_id}/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_foto(produto_id: int, foto_id: int, ctx: Editar) -> None:
    try:
        servico.remover_foto(ctx.db, produto_id, foto_id)
    except servico.ErroProduto as e:
        raise _http(e)


@router.get("/secoes", response_model=list[Secao])
def listar_secoes(ctx: Ver) -> list[Secao]:
    """As seções, cada uma com as suas subseções."""
    return [Secao.model_validate(s) for s in repo.listar_secoes(ctx.db)]


@router.post("/secoes", response_model=Secao, status_code=status.HTTP_201_CREATED)
def criar_secao(dados: NomeDados, ctx: Editar) -> Secao:
    try:
        return Secao.model_validate(servico.criar_secao(ctx.db, dados))
    except servico.ErroProduto as e:
        raise _http(e)


@router.put("/secoes/{secao_id}", response_model=Secao)
def alterar_secao(secao_id: int, dados: NomeDados, ctx: Editar) -> Secao:
    try:
        return Secao.model_validate(servico.alterar_secao(ctx.db, secao_id, dados))
    except servico.ErroProduto as e:
        raise _http(e)


@router.post("/subsecoes", response_model=Subsecao, status_code=status.HTTP_201_CREATED)
def criar_subsecao(dados: SubsecaoDados, ctx: Editar) -> Subsecao:
    try:
        return Subsecao.model_validate(servico.criar_subsecao(ctx.db, dados))
    except servico.ErroProduto as e:
        raise _http(e)


@router.put("/subsecoes/{subsecao_id}", response_model=Subsecao)
def alterar_subsecao(subsecao_id: int, dados: SubsecaoDados, ctx: Editar) -> Subsecao:
    try:
        return Subsecao.model_validate(servico.alterar_subsecao(ctx.db, subsecao_id, dados))
    except servico.ErroProduto as e:
        raise _http(e)


@router.get("/marcas", response_model=list[Marca])
def listar_marcas(ctx: Ver) -> list[Marca]:
    return [Marca.model_validate(m) for m in repo.listar_marcas(ctx.db)]


@router.post("/marcas", response_model=Marca, status_code=status.HTTP_201_CREATED)
def criar_marca(dados: NomeDados, ctx: Editar) -> Marca:
    try:
        return Marca.model_validate(servico.criar_marca(ctx.db, dados))
    except servico.ErroProduto as e:
        raise _http(e)


@router.put("/marcas/{marca_id}", response_model=Marca)
def alterar_marca(marca_id: int, dados: NomeDados, ctx: Editar) -> Marca:
    try:
        return Marca.model_validate(servico.alterar_marca(ctx.db, marca_id, dados))
    except servico.ErroProduto as e:
        raise _http(e)
