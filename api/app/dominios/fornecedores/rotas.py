from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dominios.fornecedores import repositorio as repo
from app.dominios.fornecedores import servico
from app.dominios.fornecedores.esquemas import DadosDoCnpj, Fornecedor, FornecedorDados, FornecedorResumo
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["fornecedores"])

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicado: status.HTTP_409_CONFLICT,
}


def _http(erro: servico.ErroFornecedor) -> HTTPException:
    return HTTPException(_STATUS[type(erro)], str(erro))


@router.get("/fornecedores", response_model=list[FornecedorResumo])
def listar_fornecedores(
    ctx: Annotated[Contexto, Depends(exige("fornecedores.ver"))],
    busca: Annotated[str | None, Query(description="Parte da razão social, do fantasia, de um contato ou do CNPJ")] = None,
    so_ativos: bool = False,
) -> list[FornecedorResumo]:
    """Fornecedores de todas as lojas (cadastro global)."""
    return [FornecedorResumo.model_validate(f) for f in repo.listar_fornecedores(ctx.db, busca, so_ativos)]


@router.get("/fornecedores/{fornecedor_id}", response_model=Fornecedor)
def obter_fornecedor(fornecedor_id: int, ctx: Annotated[Contexto, Depends(exige("fornecedores.ver"))]) -> Fornecedor:
    try:
        return Fornecedor.model_validate(servico.obter_fornecedor(ctx.db, fornecedor_id))
    except servico.ErroFornecedor as e:
        raise _http(e)


@router.post("/fornecedores", response_model=Fornecedor, status_code=status.HTTP_201_CREATED)
def criar_fornecedor(dados: FornecedorDados,
                     ctx: Annotated[Contexto, Depends(exige("fornecedores.editar"))]) -> Fornecedor:
    try:
        return Fornecedor.model_validate(servico.criar_fornecedor(ctx.db, dados))
    except servico.ErroFornecedor as e:
        raise _http(e)


@router.put("/fornecedores/{fornecedor_id}", response_model=Fornecedor)
def alterar_fornecedor(fornecedor_id: int, dados: FornecedorDados,
                       ctx: Annotated[Contexto, Depends(exige("fornecedores.editar"))]) -> Fornecedor:
    """Altera o cadastro. Os telefones e contatos enviados substituem os que existiam."""
    try:
        return Fornecedor.model_validate(servico.alterar_fornecedor(ctx.db, fornecedor_id, dados))
    except servico.ErroFornecedor as e:
        raise _http(e)


@router.get("/cnpj/{cnpj}", response_model=DadosDoCnpj)
def consultar_cnpj(cnpj: str, ctx: Annotated[Contexto, Depends(exige("fornecedores.editar"))]) -> DadosDoCnpj:
    """Cadastro público do CNPJ na Receita (pela BrasilAPI), para preencher a ficha do fornecedor."""
    try:
        return DadosDoCnpj.model_validate(servico.consultar_cnpj(ctx.db, cnpj), from_attributes=True)
    except servico.ErroFornecedor as e:
        raise _http(e)
    except servico.CnpjIndisponivel:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Consulta de CNPJ indisponível; preencha os dados à mão")
