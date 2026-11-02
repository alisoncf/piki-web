"""Consultas de fornecedores."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.dominios.fornecedores.modelos import ContatoFornecedor, Fornecedor
from app.nucleo.documentos import so_digitos


def listar_fornecedores(db: Session, busca: str | None = None, so_ativos: bool = False) -> list[Fornecedor]:
    consulta = select(Fornecedor).order_by(Fornecedor.nome, Fornecedor.id)
    if busca and busca.strip():
        termo = f"%{busca.strip().lower()}%"
        condicoes = [
            func.lower(Fornecedor.nome).like(termo),
            func.lower(Fornecedor.nome_fantasia).like(termo),
            Fornecedor.id.in_(select(ContatoFornecedor.fornecedor_id).where(func.lower(ContatoFornecedor.nome).like(termo))),
        ]
        if digitos := so_digitos(busca):
            condicoes.append(Fornecedor.cpf_cnpj.like(f"{digitos}%"))
        consulta = consulta.where(or_(*condicoes))
    if so_ativos:
        consulta = consulta.where(Fornecedor.ativo.is_(True))
    return list(db.scalars(consulta))


def fornecedor_por_documento(db: Session, cpf_cnpj: str) -> Fornecedor | None:
    return db.scalar(select(Fornecedor).where(Fornecedor.cpf_cnpj == cpf_cnpj))
