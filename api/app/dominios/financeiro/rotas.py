from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status

from app.dominios.financeiro import servico
from app.dominios.financeiro.esquemas import ContaPlano, ContaPlanoDados
from app.nucleo.contexto import Contexto, exige

router = APIRouter(tags=["financeiro"])

Cadastrar = Annotated[Contexto, Depends(exige("financeiro.plano"))]

_STATUS = {servico.NaoEncontrado: status.HTTP_404_NOT_FOUND, servico.Duplicado: status.HTTP_409_CONFLICT}


@router.get("/plano-contas", response_model=list[ContaPlano])
def listar(ctx: Annotated[Contexto, Depends(exige("financeiro.plano", "caixa.operar", "caixa.conferir"))],
           tipo: Literal["receita", "despesa"] | None = None, so_ativas: bool = False) -> list[ContaPlano]:
    """As contas de receita e de despesa (o caixa escolhe uma na despesa e na outra entrada)."""
    return [ContaPlano.model_validate(c) for c in servico.listar(ctx.db, tipo, so_ativas)]


@router.post("/plano-contas", response_model=ContaPlano, status_code=status.HTTP_201_CREATED)
def criar(dados: ContaPlanoDados, ctx: Cadastrar) -> ContaPlano:
    try:
        return ContaPlano.model_validate(servico.salvar(ctx.db, None, dados))
    except servico.ErroFinanceiro as e:
        raise HTTPException(_STATUS[type(e)], str(e))


@router.put("/plano-contas/{conta_id}", response_model=ContaPlano)
def alterar(conta_id: int, dados: ContaPlanoDados, ctx: Cadastrar) -> ContaPlano:
    try:
        return ContaPlano.model_validate(servico.salvar(ctx.db, conta_id, dados))
    except servico.ErroFinanceiro as e:
        raise HTTPException(_STATUS[type(e)], str(e))
