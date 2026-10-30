"""Consultas de funcionários e cargos."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.dominios.funcionarios.modelos import Cargo, Funcionario
from app.nucleo.documentos import so_digitos


def listar_funcionarios(db: Session, busca: str | None = None, empresa_id: int | None = None,
                        so_ativos: bool = False) -> list[Funcionario]:
    consulta = select(Funcionario).order_by(Funcionario.nome)
    if busca and busca.strip():
        termo = f"%{busca.strip().lower()}%"
        condicoes = [func.lower(Funcionario.nome).like(termo), func.lower(Funcionario.apelido).like(termo)]
        if digitos := so_digitos(busca):
            condicoes.append(Funcionario.cpf.like(f"%{digitos}%"))
        consulta = consulta.where(or_(*condicoes))
    if empresa_id is not None:
        consulta = consulta.where(Funcionario.empresa_id == empresa_id)
    if so_ativos:
        consulta = consulta.where(Funcionario.ativo.is_(True))
    return list(db.scalars(consulta))


def funcionario_por_cpf(db: Session, cpf: str) -> Funcionario | None:
    return db.scalar(select(Funcionario).where(Funcionario.cpf == cpf))


def listar_cargos(db: Session) -> list[Cargo]:
    return list(db.scalars(select(Cargo).order_by(Cargo.nome)))


def cargo_por_nome(db: Session, nome: str) -> Cargo | None:
    return db.scalar(select(Cargo).where(func.lower(Cargo.nome) == nome.strip().lower()))
