"""Consultas das notas de entrada."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.dominios.entradas.modelos import NotaEntrada
from app.dominios.fornecedores.modelos import Fornecedor
from app.nucleo.documentos import so_digitos


def listar_notas(db: Session, empresa_id: int, busca: str | None = None, situacao: str | None = None,
                 limite: int = 50, deslocamento: int = 0) -> tuple[list[NotaEntrada], int]:
    """As notas da loja, da carregada por último para a primeira."""
    consulta = select(NotaEntrada).where(NotaEntrada.empresa_id == empresa_id)
    if busca and busca.strip():
        termo = busca.strip()
        condicoes = [NotaEntrada.fornecedor_id.in_(select(Fornecedor.id).where(or_(
            func.lower(Fornecedor.nome).like(f"%{termo.lower()}%"),
            func.lower(Fornecedor.nome_fantasia).like(f"%{termo.lower()}%"))))]
        if (digitos := so_digitos(termo)) and digitos == termo:
            condicoes.append(NotaEntrada.chave == digitos)
            if len(digitos) <= 9:
                condicoes.append(NotaEntrada.numero == int(digitos))
        consulta = consulta.where(or_(*condicoes))
    if situacao:
        consulta = consulta.where(NotaEntrada.situacao == situacao)
    total = db.scalar(select(func.count()).select_from(consulta.subquery()))
    itens = db.scalars(consulta.order_by(NotaEntrada.id.desc()).limit(limite).offset(deslocamento))
    return list(itens), total
