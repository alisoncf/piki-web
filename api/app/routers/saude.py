from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import configuracao
from app.db import sessao
from app.filial import cod_emp_atual

router = APIRouter(tags=["saúde"])


@router.get("/saude")
def saude(
    resposta: Response,
    db: Annotated[Session, Depends(sessao)],
    cod_emp: Annotated[str, Depends(cod_emp_atual)],
) -> dict:
    """Confirma que a API está no ar e consegue falar com o banco."""
    try:
        db.execute(text("SELECT 1"))
        banco = "ok"
    except SQLAlchemyError:
        banco = "indisponível"
        resposta.status_code = 503
    return {
        "status": "ok" if banco == "ok" else "erro",
        "banco": banco,
        "cod_emp": cod_emp,
        "ambiente": configuracao().ambiente,
    }
