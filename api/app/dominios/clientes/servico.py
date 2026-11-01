"""Regras do cadastro de clientes, setores, órgãos e grupos."""
import uuid
from datetime import date
from pathlib import PurePath

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dominios.cidades.modelos import Cidade
from app.dominios.clientes import repositorio as repo
from app.dominios.clientes.esquemas import (
    AnotacaoDados, ClienteDados, GrupoClienteDados, OrgaoDados, ParentescoDados, SetorDados,
)
from app.dominios.clientes.modelos import (
    AnotacaoCliente, Cliente, DocumentoCliente, GrupoCliente, Orgao, Parentesco, ReferenciaCliente, Setor,
    TelefoneCliente,
)
from app.dominios.funcionarios.modelos import Funcionario
from app.nucleo.arquivos import Armazenamento
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

def _conferir_setor(db: Session, dados: SetorDados, setor_id: int | None) -> list[Funcionario]:
    _existe(db, Cidade, dados.cidade_id, "Cidade não encontrada")
    outro = repo.setor_por_nome(db, dados.nome, dados.cidade_id)
    if outro and outro.id != setor_id:
        raise Duplicado(f"Já existe o setor {outro.nome}" + (f" em {outro.cidade.nome}" if outro.cidade else ""))
    cobradores = []
    for cobrador_id in dict.fromkeys(dados.cobradores):  # sem repetir, na ordem enviada
        cobrador = db.get(Funcionario, cobrador_id)
        if cobrador is None:
            raise DadoInvalido("Cobrador não encontrado")
        cobradores.append(cobrador)
    return cobradores


def _aplicar_setor(setor: Setor, dados: SetorDados, cobradores: list[Funcionario]) -> None:
    for campo, valor in dados.model_dump(exclude={"cobradores"}).items():
        setattr(setor, campo, valor)
    setor.cobradores = cobradores


def obter_setor(db: Session, setor_id: int) -> Setor:
    setor = db.get(Setor, setor_id)
    if setor is None:
        raise NaoEncontrado("Setor não encontrado")
    return setor


def criar_setor(db: Session, dados: SetorDados) -> Setor:
    cobradores = _conferir_setor(db, dados, None)
    setor = Setor()
    _aplicar_setor(setor, dados, cobradores)
    db.add(setor)
    db.commit()
    db.refresh(setor)
    return setor


def alterar_setor(db: Session, setor_id: int, dados: SetorDados) -> Setor:
    setor = obter_setor(db, setor_id)
    cobradores = _conferir_setor(db, dados, setor_id)
    _aplicar_setor(setor, dados, cobradores)
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


# documentos (crediário)

TIPOS_DE_DOCUMENTO = {
    "identidade": "Identidade (RG ou CNH)",
    "cpf": "CPF",
    "endereco": "Comprovante de endereço",
    "renda": "Comprovante de renda",
    "contrato": "Ficha ou contrato de crediário assinado",
    "foto": "Foto do cliente",
    "outro": "Outro",
}
TAMANHO_MAXIMO_DOCUMENTO = 5 * 1024 * 1024
# reconhecidos pelo começo do arquivo, não pelo nome
_FORMATOS = {b"%PDF-": ("application/pdf", ".pdf"), b"\x89PNG\r\n\x1a\n": ("image/png", ".png"),
             b"\xff\xd8\xff": ("image/jpeg", ".jpg")}


def _documento(db: Session, cliente_id: int, documento_id: int) -> DocumentoCliente:
    documento = db.get(DocumentoCliente, documento_id)
    if documento is None or documento.cliente_id != cliente_id or documento.removido_em is not None:
        raise NaoEncontrado("Documento não encontrado")
    return documento


def listar_documentos(db: Session, cliente_id: int) -> list[DocumentoCliente]:
    return repo.documentos_do_cliente(db, obter_cliente(db, cliente_id).id)


def enviar_documento(db: Session, arquivos: Armazenamento, cliente_id: int, tipo: str, descricao: str | None,
                     nome_arquivo: str | None, conteudo: bytes, usuario_id: int, empresa_id: int) -> DocumentoCliente:
    cliente = obter_cliente(db, cliente_id)
    if tipo not in TIPOS_DE_DOCUMENTO:
        raise DadoInvalido(f"Tipo de documento desconhecido: {tipo}")
    if not conteudo:
        raise DadoInvalido("Arquivo vazio")
    if len(conteudo) > TAMANHO_MAXIMO_DOCUMENTO:
        raise DadoInvalido("O arquivo passa de 5 MB")
    formato = next((f for inicio, f in _FORMATOS.items() if conteudo.startswith(inicio)), None)
    if formato is None:
        raise DadoInvalido("Envie um PDF ou uma imagem JPEG ou PNG")
    tipo_conteudo, extensao = formato
    chave = f"clientes/{cliente.id}/{uuid.uuid4().hex}{extensao}"
    arquivos.gravar(chave, conteudo, tipo_conteudo)
    documento = DocumentoCliente(
        cliente_id=cliente.id, tipo=tipo, descricao=(descricao or "").strip()[:60] or None,
        nome_arquivo=PurePath((nome_arquivo or "").replace("\\", "/")).name[:120] or f"documento{extensao}",
        tipo_conteudo=tipo_conteudo, tamanho=len(conteudo), chave=chave, usuario_id=usuario_id, empresa_id=empresa_id,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento


def ler_documento(db: Session, arquivos: Armazenamento, cliente_id: int, documento_id: int) -> tuple[DocumentoCliente, bytes]:
    documento = _documento(db, cliente_id, documento_id)
    return documento, arquivos.ler(documento.chave)


def remover_documento(db: Session, cliente_id: int, documento_id: int, usuario_id: int) -> None:
    """Tira da lista; o registro e o arquivo ficam, com quem removeu e quando."""
    documento = _documento(db, cliente_id, documento_id)
    documento.removido_em = func.now()
    documento.removido_por_id = usuario_id
    db.commit()

