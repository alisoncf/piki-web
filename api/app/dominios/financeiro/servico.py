"""Regras do plano de contas."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominios.financeiro.esquemas import ContaPlanoDados
from app.dominios.financeiro.modelos import ContaPlano


class ErroFinanceiro(Exception):
    """Erro de regra do financeiro; a mensagem vai para o usuário."""


class NaoEncontrado(ErroFinanceiro):
    pass


class Duplicado(ErroFinanceiro):
    pass


def listar(db: Session, tipo: str | None = None, so_ativas: bool = False) -> list[ContaPlano]:
    consulta = select(ContaPlano).order_by(ContaPlano.tipo.desc(), ContaPlano.nome)
    if tipo:
        consulta = consulta.where(ContaPlano.tipo == tipo)
    if so_ativas:
        consulta = consulta.where(ContaPlano.ativo.is_(True))
    return list(db.scalars(consulta))


def salvar(db: Session, conta_id: int | None, dados: ContaPlanoDados) -> ContaPlano:
    conta = db.get(ContaPlano, conta_id) if conta_id else ContaPlano()
    if conta is None:
        raise NaoEncontrado("Conta não encontrada")
    nome = dados.nome.strip()
    outra = db.scalar(select(ContaPlano).where(ContaPlano.tipo == dados.tipo, func.lower(ContaPlano.nome) == nome.lower(),
                                               ContaPlano.id != (conta.id or 0)))
    if outra is not None:
        raise Duplicado(f"Já existe a conta de {dados.tipo} {outra.nome}")
    conta.tipo, conta.nome, conta.ativo = dados.tipo, nome, dados.ativo
    db.add(conta)
    db.commit()
    return conta
