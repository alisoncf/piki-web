"""Regras do cadastro de clientes, setores, órgãos e grupos."""
from datetime import date

from sqlalchemy.orm import Session

from app.dominios.acesso.modelos import Empresa
from app.dominios.clientes import repositorio as repo
from app.dominios.clientes.esquemas import (
    AnotacaoDados, ClienteDados, GrupoClienteDados, OrgaoDados, ParentescoDados, SetorDados,
)
from app.dominios.clientes.modelos import (
    AnotacaoCliente, Cliente, GrupoCliente, Orgao, Parentesco, ReferenciaCliente, Setor, SetorCobrador,
    TelefoneCliente,
)
from app.dominios.funcionarios.modelos import Funcionario
from app.nucleo.documentos import cpf_cnpj_valido


class ErroCliente(Exception):
    """Erro de regra do cadastro; a mensagem vai para o usuário."""


class NaoEncontrado(ErroCliente):
    pass


class DadoInvalido(ErroCliente):
    pass


class Duplicado(ErroCliente):
    pass


def _existe(db: Session, modelo: type, id_: int | None, mensagem: str) -> None:
    if id_ is not None and db.get(modelo, id_) is None:
        raise DadoInvalido(mensagem)


# clientes

def _conferir(db: Session, dados: ClienteDados, cliente_id: int | None) -> None:
    if dados.cpf_cnpj:
        tamanho = 11 if dados.tipo == "F" else 14
        if len(dados.cpf_cnpj) != tamanho or not cpf_cnpj_valido(dados.cpf_cnpj):
            raise DadoInvalido("CPF inválido" if dados.tipo == "F" else "CNPJ inválido")
        outro = repo.cliente_por_documento(db, dados.cpf_cnpj)
        if outro and outro.id != cliente_id:
            raise Duplicado(f"Já existe um cliente com este {'CPF' if dados.tipo == 'F' else 'CNPJ'}: {outro.nome}")
    _existe(db, Setor, dados.setor_id, "Setor não encontrado")
    _existe(db, Setor, dados.setor_trabalho_id, "Setor do trabalho não encontrado")
    _existe(db, Orgao, dados.orgao_id, "Órgão não encontrado")
    _existe(db, GrupoCliente, dados.grupo_id, "Grupo não encontrado")
    for ref in dados.referencias:
        _existe(db, Parentesco, ref.parentesco_id, "Parentesco não encontrado")
    numeros = [t.numero for t in dados.telefones]
    if len(numeros) != len(set(numeros)):
        raise DadoInvalido("Telefone repetido")


def _aplicar(cliente: Cliente, dados: ClienteDados) -> None:
    for campo, valor in dados.model_dump(exclude={"telefones", "referencias"}).items():
        setattr(cliente, campo, valor)
    cliente.telefones = [TelefoneCliente(numero=t.numero, tipo=t.tipo) for t in dados.telefones]
    cliente.referencias = [ReferenciaCliente(**r.model_dump()) for r in dados.referencias]
    cliente.data_alteracao = date.today()


def obter_cliente(db: Session, cliente_id: int) -> Cliente:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise NaoEncontrado("Cliente não encontrado")
    return cliente


def criar_cliente(db: Session, dados: ClienteDados, empresa_id: int) -> Cliente:
    _conferir(db, dados, None)
    cliente = Cliente(empresa_cadastro_id=empresa_id, data_cadastro=date.today())
    _aplicar(cliente, dados)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def alterar_cliente(db: Session, cliente_id: int, dados: ClienteDados) -> Cliente:
    cliente = obter_cliente(db, cliente_id)
    _conferir(db, dados, cliente_id)
    _aplicar(cliente, dados)
    db.commit()
    db.refresh(cliente)
    return cliente


def anotar(db: Session, cliente_id: int, dados: AnotacaoDados, usuario_id: int, empresa_id: int) -> Cliente:
    cliente = obter_cliente(db, cliente_id)
    cliente.anotacoes.append(AnotacaoCliente(texto=dados.texto, usuario_id=usuario_id, empresa_id=empresa_id))
    db.commit()
    db.refresh(cliente)
    return cliente


# setores

def _conferir_setor(db: Session, dados: SetorDados, setor_id: int | None) -> None:
    outro = repo.setor_por_nome(db, dados.nome, dados.cidade)
    if outro and outro.id != setor_id:
        raise Duplicado(f"Já existe o setor {outro.nome}" + (f" em {outro.cidade}" if outro.cidade else ""))
    empresas = [c.empresa_id for c in dados.cobradores]
    if len(empresas) != len(set(empresas)):
        raise DadoInvalido("Só pode haver um cobrador por loja")
    for c in dados.cobradores:
        _existe(db, Empresa, c.empresa_id, "Loja não encontrada")
        _existe(db, Funcionario, c.funcionario_id, "Cobrador não encontrado")


def _aplicar_setor(setor: Setor, dados: SetorDados) -> None:
    for campo, valor in dados.model_dump(exclude={"cobradores"}).items():
        setattr(setor, campo, valor)
    atuais = {c.empresa_id: c for c in setor.cobradores}
    novos = []
    for c in dados.cobradores:
        cobrador = atuais.get(c.empresa_id) or SetorCobrador(empresa_id=c.empresa_id)
        cobrador.funcionario_id = c.funcionario_id
        novos.append(cobrador)
    setor.cobradores = novos


def obter_setor(db: Session, setor_id: int) -> Setor:
    setor = db.get(Setor, setor_id)
    if setor is None:
        raise NaoEncontrado("Setor não encontrado")
    return setor


def criar_setor(db: Session, dados: SetorDados) -> Setor:
    _conferir_setor(db, dados, None)
    setor = Setor()
    _aplicar_setor(setor, dados)
    db.add(setor)
    db.commit()
    db.refresh(setor)
    return setor


def alterar_setor(db: Session, setor_id: int, dados: SetorDados) -> Setor:
    setor = obter_setor(db, setor_id)
    _conferir_setor(db, dados, setor_id)
    _aplicar_setor(setor, dados)
    db.commit()
    db.refresh(setor)
    return setor


# órgãos

def _conferir_orgao(db: Session, dados: OrgaoDados, orgao_id: int | None) -> None:
    outro = repo.orgao_por_nome(db, dados.nome)
    if outro and outro.id != orgao_id:
        raise Duplicado(f"Já existe o órgão {outro.nome}")
    _existe(db, GrupoCliente, dados.grupo_id, "Grupo não encontrado")
    _existe(db, Setor, dados.setor_id, "Setor não encontrado")


def criar_orgao(db: Session, dados: OrgaoDados) -> Orgao:
    _conferir_orgao(db, dados, None)
    orgao = Orgao(**dados.model_dump())
    db.add(orgao)
    db.commit()
    db.refresh(orgao)
    return orgao


def alterar_orgao(db: Session, orgao_id: int, dados: OrgaoDados) -> Orgao:
    orgao = db.get(Orgao, orgao_id)
    if orgao is None:
        raise NaoEncontrado("Órgão não encontrado")
    _conferir_orgao(db, dados, orgao_id)
    for campo, valor in dados.model_dump().items():
        setattr(orgao, campo, valor)
    db.commit()
    db.refresh(orgao)
    return orgao


# grupos

def _conferir_grupo(db: Session, dados: GrupoClienteDados, grupo_id: int | None) -> None:
    outro = repo.grupo_por_nome(db, dados.nome)
    if outro and outro.id != grupo_id:
        raise Duplicado(f"Já existe o grupo {outro.nome}")


def criar_grupo(db: Session, dados: GrupoClienteDados) -> GrupoCliente:
    _conferir_grupo(db, dados, None)
    grupo = GrupoCliente(**dados.model_dump())
    db.add(grupo)
    db.commit()
    return grupo


def alterar_grupo(db: Session, grupo_id: int, dados: GrupoClienteDados) -> GrupoCliente:
    grupo = db.get(GrupoCliente, grupo_id)
    if grupo is None:
        raise NaoEncontrado("Grupo não encontrado")
    _conferir_grupo(db, dados, grupo_id)
    for campo, valor in dados.model_dump().items():
        setattr(grupo, campo, valor)
    db.commit()
    return grupo


# parentescos

def _conferir_parentesco(db: Session, dados: ParentescoDados, parentesco_id: int | None) -> None:
    outro = repo.parentesco_por_nome(db, dados.nome)
    if outro and outro.id != parentesco_id:
        raise Duplicado(f"Já existe o parentesco {outro.nome}")


def criar_parentesco(db: Session, dados: ParentescoDados) -> Parentesco:
    _conferir_parentesco(db, dados, None)
    parentesco = Parentesco(**dados.model_dump())
    db.add(parentesco)
    db.commit()
    return parentesco


def alterar_parentesco(db: Session, parentesco_id: int, dados: ParentescoDados) -> Parentesco:
    parentesco = db.get(Parentesco, parentesco_id)
    if parentesco is None:
        raise NaoEncontrado("Parentesco não encontrado")
    _conferir_parentesco(db, dados, parentesco_id)
    for campo, valor in dados.model_dump().items():
        setattr(parentesco, campo, valor)
    db.commit()
    return parentesco
