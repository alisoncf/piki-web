from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dominios.funcionarios import repositorio as repo
from app.dominios.funcionarios import servico
from app.dominios.funcionarios.esquemas import Cargo, CargoDados, Funcionario, FuncionarioDados, FuncionarioResumo
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["funcionários"])

_STATUS = {
    servico.NaoEncontrado: status.HTTP_404_NOT_FOUND,
    servico.DadoInvalido: status.HTTP_422_UNPROCESSABLE_CONTENT,
    servico.Duplicado: status.HTTP_409_CONFLICT,
}


def _http(erro: servico.ErroFuncionario) -> HTTPException:
    return HTTPException(_STATUS[type(erro)], str(erro))


@router.get("/funcionarios", response_model=list[FuncionarioResumo])
def listar_funcionarios(
    # o caixa escolhe o funcionário do vale e da comissão
    ctx: Annotated[Contexto, Depends(exige("funcionarios.ver", "caixa.operar"))],
    busca: Annotated[str | None, Query(description="Parte do nome, do apelido ou do CPF")] = None,
    empresa_id: Annotated[int | None, Query(description="Só os lotados nesta loja")] = None,
    so_ativos: bool = False,
) -> list[FuncionarioResumo]:
    """Funcionários de todas as lojas (cadastro global), com filtros opcionais."""
    return [FuncionarioResumo.model_validate(f) for f in repo.listar_funcionarios(ctx.db, busca, empresa_id, so_ativos)]


@router.get("/funcionarios/{funcionario_id}", response_model=Funcionario)
def obter_funcionario(funcionario_id: int, ctx: Annotated[Contexto, Depends(exige("funcionarios.ver"))]) -> Funcionario:
    try:
        return Funcionario.model_validate(servico.obter_funcionario(ctx.db, funcionario_id))
    except servico.ErroFuncionario as e:
        raise _http(e)


@router.post("/funcionarios", response_model=Funcionario, status_code=status.HTTP_201_CREATED)
def criar_funcionario(dados: FuncionarioDados,
                      ctx: Annotated[Contexto, Depends(exige("funcionarios.editar"))]) -> Funcionario:
    try:
        return Funcionario.model_validate(servico.criar_funcionario(ctx.db, dados))
    except servico.ErroFuncionario as e:
        raise _http(e)


@router.put("/funcionarios/{funcionario_id}", response_model=Funcionario)
def alterar_funcionario(funcionario_id: int, dados: FuncionarioDados,
                        ctx: Annotated[Contexto, Depends(exige("funcionarios.editar"))]) -> Funcionario:
    """Altera o cadastro. Os telefones enviados substituem os que existiam."""
    try:
        return Funcionario.model_validate(servico.alterar_funcionario(ctx.db, funcionario_id, dados))
    except servico.ErroFuncionario as e:
        raise _http(e)


@router.get("/cargos", response_model=list[Cargo])
def listar_cargos(ctx: Annotated[Contexto, Depends(exige("funcionarios.ver"))]) -> list[Cargo]:
    return [Cargo.model_validate(c) for c in repo.listar_cargos(ctx.db)]


@router.post("/cargos", response_model=Cargo, status_code=status.HTTP_201_CREATED)
def criar_cargo(dados: CargoDados, ctx: Annotated[Contexto, Depends(exige("funcionarios.editar"))]) -> Cargo:
    try:
        return Cargo.model_validate(servico.criar_cargo(ctx.db, dados))
    except servico.ErroFuncionario as e:
        raise _http(e)


@router.put("/cargos/{cargo_id}", response_model=Cargo)
def alterar_cargo(cargo_id: int, dados: CargoDados,
                  ctx: Annotated[Contexto, Depends(exige("funcionarios.editar"))]) -> Cargo:
    try:
        return Cargo.model_validate(servico.alterar_cargo(ctx.db, cargo_id, dados))
    except servico.ErroFuncionario as e:
        raise _http(e)
