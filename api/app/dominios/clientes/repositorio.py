"""Consultas de clientes, setores, órgãos e grupos."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.dominios.clientes.modelos import (
    Cliente, DocumentoCliente, GrupoCliente, Orgao, Parentesco, Setor, TelefoneCliente,
)
from app.nucleo.documentos import so_digitos


def listar_clientes(db: Session, busca: str | None = None, setor_id: int | None = None,
                    orgao_id: int | None = None, bloqueado: bool | None = None,
                    limite: int = 50, deslocamento: int = 0) -> tuple[list[Cliente], int]:
    """Uma página de clientes em ordem de nome, e o total que atende aos filtros."""
    consulta = select(Cliente)
    if busca and busca.strip():
        condicoes = [func.lower(Cliente.nome).like(f"%{busca.strip().lower()}%")]
        if digitos := so_digitos(busca):
            condicoes.append(Cliente.cpf_cnpj.like(f"{digitos}%"))
            if len(digitos) >= 8:
                condicoes.append(Cliente.id.in_(
                    select(TelefoneCliente.cliente_id).where(TelefoneCliente.numero.like(f"%{digitos}"))
                ))
        consulta = consulta.where(or_(*condicoes))
    if setor_id is not None:
        consulta = consulta.where(Cliente.setor_id == setor_id)
    if orgao_id is not None:
        consulta = consulta.where(Cliente.orgao_id == orgao_id)
    if bloqueado is not None:
        consulta = consulta.where(Cliente.bloqueado.is_(bloqueado))
    total = db.scalar(select(func.count()).select_from(consulta.subquery()))
    itens = db.scalars(consulta.order_by(Cliente.nome, Cliente.id).limit(limite).offset(deslocamento))
    return list(itens), total


def cliente_por_documento(db: Session, cpf_cnpj: str) -> Cliente | None:
    return db.scalar(select(Cliente).where(Cliente.cpf_cnpj == cpf_cnpj))


def listar_setores(db: Session, busca: str | None = None) -> list[Setor]:
    consulta = select(Setor).order_by(Setor.nome, Setor.cidade_id)
    if busca and busca.strip():
        consulta = consulta.where(func.lower(Setor.nome).like(f"%{busca.strip().lower()}%"))
    return list(db.scalars(consulta))


def setor_por_nome(db: Session, nome: str, cidade_id: int | None) -> Setor | None:
    consulta = select(Setor).where(func.lower(Setor.nome) == nome.strip().lower())
    if cidade_id is not None:
        consulta = consulta.where(Setor.cidade_id == cidade_id)
    else:
        consulta = consulta.where(Setor.cidade_id.is_(None))
    return db.scalar(consulta)


def listar_orgaos(db: Session, busca: str | None = None) -> list[Orgao]:
    consulta = select(Orgao).order_by(Orgao.nome)
    if busca and busca.strip():
        consulta = consulta.where(func.lower(Orgao.nome).like(f"%{busca.strip().lower()}%"))
    return list(db.scalars(consulta))


def orgao_por_nome(db: Session, nome: str) -> Orgao | None:
    return db.scalar(select(Orgao).where(func.lower(Orgao.nome) == nome.strip().lower()))


def listar_grupos(db: Session) -> list[GrupoCliente]:
    return list(db.scalars(select(GrupoCliente).order_by(GrupoCliente.nome)))


def grupo_por_nome(db: Session, nome: str) -> GrupoCliente | None:
    return db.scalar(select(GrupoCliente).where(func.lower(GrupoCliente.nome) == nome.strip().lower()))


def listar_parentescos(db: Session) -> list[Parentesco]:
    return list(db.scalars(select(Parentesco).order_by(Parentesco.nome)))


def parentesco_por_nome(db: Session, nome: str) -> Parentesco | None:
    return db.scalar(select(Parentesco).where(func.lower(Parentesco.nome) == nome.strip().lower()))


def documentos_do_cliente(db: Session, cliente_id: int) -> list[DocumentoCliente]:
    """Os que não foram removidos, do mais novo para o mais antigo."""
    return list(db.scalars(
        select(DocumentoCliente)
        .where(DocumentoCliente.cliente_id == cliente_id, DocumentoCliente.removido_em.is_(None))
        .order_by(DocumentoCliente.data_hora.desc(), DocumentoCliente.id.desc())
    ))

