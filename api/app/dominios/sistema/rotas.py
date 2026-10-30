from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import configuracao
from app.nucleo.banco import sessao

router = APIRouter(tags=["sistema"])


@router.get("/saude")
def saude(resposta: Response, db: Annotated[Session, Depends(sessao)]) -> dict:
    """Confirma que a API está no ar e consegue falar com o banco."""
    try:
        db.execute(text("SELECT 1"))
        banco = "ok"
    except SQLAlchemyError:
        banco = "indisponível"
        resposta.status_code = 503
    return {"status": "ok" if banco == "ok" else "erro", "banco": banco, "ambiente": configuracao().ambiente}
