"""Regras do cadastro de funcionários e cargos."""
from sqlalchemy.orm import Session

from app.dominios.acesso.modelos import Empresa
from app.dominios.clientes.modelos import Setor
from app.dominios.funcionarios import repositorio as repo
from app.dominios.funcionarios.esquemas import CargoDados, FuncionarioDados
from app.dominios.funcionarios.modelos import Cargo, Funcionario, TelefoneFuncionario
from app.nucleo.documentos import cpf_valido


class ErroFuncionario(Exception):
    """Erro de regra do cadastro; a mensagem vai para o usuário."""


class NaoEncontrado(ErroFuncionario):
    pass


class DadoInvalido(ErroFuncionario):
    pass


class Duplicado(ErroFuncionario):
    pass


def _conferir(db: Session, dados: FuncionarioDados, funcionario_id: int | None) -> None:
    if dados.cpf:
        if not cpf_valido(dados.cpf):
            raise DadoInvalido("CPF inválido")
        outro = repo.funcionario_por_cpf(db, dados.cpf)
        if outro and outro.id != funcionario_id:
            raise Duplicado(f"Já existe um funcionário com este CPF: {outro.nome}")
    if db.get(Empresa, dados.empresa_id) is None:
        raise DadoInvalido("Loja não encontrada")
    if dados.cargo_id is not None and db.get(Cargo, dados.cargo_id) is None:
        raise DadoInvalido("Cargo não encontrado")
    if dados.setor_id is not None and db.get(Setor, dados.setor_id) is None:
        raise DadoInvalido("Setor não encontrado")
    numeros = [t.numero for t in dados.telefones]
    if len(numeros) != len(set(numeros)):
        raise DadoInvalido("Telefone repetido")


def _aplicar(funcionario: Funcionario, dados: FuncionarioDados) -> None:
    for campo, valor in dados.model_dump(exclude={"telefones"}).items():
        setattr(funcionario, campo, valor)
    funcionario.telefones = [TelefoneFuncionario(numero=t.numero, tipo=t.tipo) for t in dados.telefones]


def obter_funcionario(db: Session, funcionario_id: int) -> Funcionario:
    funcionario = db.get(Funcionario, funcionario_id)
    if funcionario is None:
        raise NaoEncontrado("Funcionário não encontrado")
    return funcionario


def criar_funcionario(db: Session, dados: FuncionarioDados) -> Funcionario:
    _conferir(db, dados, None)
    funcionario = Funcionario()
    _aplicar(funcionario, dados)
    db.add(funcionario)
    db.commit()
    db.refresh(funcionario)
    return funcionario


def alterar_funcionario(db: Session, funcionario_id: int, dados: FuncionarioDados) -> Funcionario:
    funcionario = obter_funcionario(db, funcionario_id)
    _conferir(db, dados, funcionario_id)
    _aplicar(funcionario, dados)
    db.commit()
    db.refresh(funcionario)
    return funcionario


def _conferir_cargo(db: Session, dados: CargoDados, cargo_id: int | None) -> None:
    outro = repo.cargo_por_nome(db, dados.nome)
    if outro and outro.id != cargo_id:
        raise Duplicado(f"Já existe o cargo {outro.nome}")


def criar_cargo(db: Session, dados: CargoDados) -> Cargo:
    _conferir_cargo(db, dados, None)
    cargo = Cargo(**dados.model_dump())
    db.add(cargo)
    db.commit()
    return cargo


def alterar_cargo(db: Session, cargo_id: int, dados: CargoDados) -> Cargo:
    cargo = db.get(Cargo, cargo_id)
    if cargo is None:
        raise NaoEncontrado("Cargo não encontrado")
    _conferir_cargo(db, dados, cargo_id)
    for campo, valor in dados.model_dump().items():
        setattr(cargo, campo, valor)
    db.commit()
    return cargo
