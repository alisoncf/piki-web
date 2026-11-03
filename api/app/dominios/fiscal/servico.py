"""Regras das notas fiscais (D29). Por enquanto, a numeração."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominios.fiscal.modelos import NumeracaoNota


def numeracoes(db: Session, empresa_id: int) -> list[NumeracaoNota]:
    return list(db.scalars(select(NumeracaoNota).where(NumeracaoNota.empresa_id == empresa_id)
                           .order_by(NumeracaoNota.modelo.desc(), NumeracaoNota.serie)))


def proximo_numero(db: Session, empresa_id: int, modelo: str, serie: int) -> int:
    """Reserva o próximo número da série (trava a linha até o fim da transação: dois caixas não pegam o mesmo).
    Quem chama grava."""
    numeracao = db.scalar(select(NumeracaoNota).where(
        NumeracaoNota.empresa_id == empresa_id, NumeracaoNota.modelo == modelo, NumeracaoNota.serie == serie)
        .with_for_update())
    if numeracao is None:
        numeracao = NumeracaoNota(empresa_id=empresa_id, modelo=modelo, serie=serie, ultimo=0)
        db.add(numeracao)
    numeracao.ultimo += 1
    db.flush()
    return numeracao.ultimo


def continuar_de(db: Session, empresa_id: int, modelo: str, serie: int, ultimo: int) -> bool:
    """A numeração continua de onde o VB6 parou: só sobe, nunca volta. Devolve se mudou."""
    numeracao = db.scalar(select(NumeracaoNota).where(
        NumeracaoNota.empresa_id == empresa_id, NumeracaoNota.modelo == modelo, NumeracaoNota.serie == serie))
    if numeracao is None:
        db.add(NumeracaoNota(empresa_id=empresa_id, modelo=modelo, serie=serie, ultimo=ultimo))
        return True
    if ultimo > numeracao.ultimo:
        numeracao.ultimo = ultimo
        return True
    return False
