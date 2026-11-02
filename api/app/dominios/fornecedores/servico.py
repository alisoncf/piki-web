"""Regras do cadastro de fornecedores (D22)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominios.cidades.modelos import Cidade, nome_de_busca
from app.dominios.fornecedores import brasilapi
from app.dominios.fornecedores import repositorio as repo
from app.dominios.fornecedores.esquemas import FornecedorDados
from app.dominios.fornecedores.modelos import ContatoFornecedor, Fornecedor, TelefoneFornecedor
from app.nucleo.documentos import cnpj_valido, cpf_cnpj_valido, so_digitos
from app.nucleo.textos import nome_proprio

CnpjIndisponivel = brasilapi.CnpjIndisponivel


class ErroFornecedor(Exception):
    """Erro de regra do cadastro; a mensagem vai para o usuário."""


class NaoEncontrado(ErroFornecedor):
    pass


class DadoInvalido(ErroFornecedor):
    pass


class Duplicado(ErroFornecedor):
    pass


def _conferir(db: Session, dados: FornecedorDados, fornecedor_id: int | None) -> None:
    if not cpf_cnpj_valido(dados.cpf_cnpj):
        raise DadoInvalido("CPF/CNPJ inválido")
    outro = repo.fornecedor_por_documento(db, dados.cpf_cnpj)
    if outro and outro.id != fornecedor_id:
        raise Duplicado(f"Já existe um fornecedor com este CPF/CNPJ: {outro.nome}")
    if dados.cidade_id is not None and db.get(Cidade, dados.cidade_id) is None:
        raise DadoInvalido("Cidade não encontrada")
    numeros = [t.numero for t in dados.telefones]
    if len(numeros) != len(set(numeros)):
        raise DadoInvalido("Telefone repetido")


def _aplicar(fornecedor: Fornecedor, dados: FornecedorDados) -> None:
    for campo, valor in dados.model_dump(exclude={"telefones", "contatos"}).items():
        setattr(fornecedor, campo, valor)
    fornecedor.telefones = [TelefoneFornecedor(numero=t.numero, tipo=t.tipo) for t in dados.telefones]
    fornecedor.contatos = [ContatoFornecedor(**c.model_dump()) for c in dados.contatos]


def obter_fornecedor(db: Session, fornecedor_id: int) -> Fornecedor:
    fornecedor = db.get(Fornecedor, fornecedor_id)
    if fornecedor is None:
        raise NaoEncontrado("Fornecedor não encontrado")
    return fornecedor


def criar_fornecedor(db: Session, dados: FornecedorDados) -> Fornecedor:
    _conferir(db, dados, None)
    fornecedor = Fornecedor()
    _aplicar(fornecedor, dados)
    db.add(fornecedor)
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


def alterar_fornecedor(db: Session, fornecedor_id: int, dados: FornecedorDados) -> Fornecedor:
    """Os telefones e contatos enviados substituem os que existiam."""
    fornecedor = obter_fornecedor(db, fornecedor_id)
    _conferir(db, dados, fornecedor_id)
    _aplicar(fornecedor, dados)
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


def _cidade(db: Session, dados: dict) -> Cidade | None:
    """Pelo código do IBGE; se não vier, pelo nome e a UF."""
    codigo = so_digitos(dados.get("codigo_municipio_ibge"))
    if codigo:
        cidade = db.scalar(select(Cidade).where(Cidade.codigo_ibge == codigo))
        if cidade:
            return cidade
    nome = nome_de_busca(dados.get("municipio"))
    if not nome:
        return None
    return db.scalar(select(Cidade).where(Cidade.nome_busca == nome, Cidade.uf == (dados.get("uf") or "").upper()))


def _texto(valor: object) -> str | None:
    return (str(valor).strip() or None) if valor is not None else None


def _corta(valor: str | None, tamanho: int) -> str | None:
    """Do tamanho dos campos da ficha: o complemento da Receita às vezes é bem maior."""
    return valor[:tamanho].rstrip() if valor else None


def consultar_cnpj(db: Session, cnpj: str) -> dict:
    """O cadastro do CNPJ na Receita (pela BrasilAPI), no formato da ficha, e se ele já é fornecedor.

    A Receita escreve tudo em maiúsculas; os nomes vêm com maiúscula só nas iniciais.
    """
    cnpj = so_digitos(cnpj)
    if not cnpj_valido(cnpj):
        raise DadoInvalido("CNPJ inválido")
    dados = brasilapi.consultar(cnpj)
    if dados is None:
        raise NaoEncontrado("CNPJ não encontrado na Receita")
    # a BrasilAPI separa o tipo ("RUA") do nome do logradouro
    logradouro = nome_proprio(" ".join(p for p in (_texto(dados.get("descricao_tipo_de_logradouro")),
                                                   _texto(dados.get("logradouro"))) if p))
    telefones = [t for t in (so_digitos(dados.get(c)) for c in ("ddd_telefone_1", "ddd_telefone_2")) if len(t) >= 10]
    existente = repo.fornecedor_por_documento(db, cnpj)
    return {
        "cnpj": cnpj,
        "razao_social": _corta(nome_proprio(_texto(dados.get("razao_social"))), 100),
        "nome_fantasia": _corta(nome_proprio(_texto(dados.get("nome_fantasia"))), 60),
        "situacao": _texto(dados.get("descricao_situacao_cadastral")),
        "cep": so_digitos(dados.get("cep")) or None,
        "logradouro": _corta(logradouro, 60),
        "numero": _corta(_texto(dados.get("numero")), 10),
        "complemento": _corta(nome_proprio(_texto(dados.get("complemento"))), 60),
        "bairro": _corta(nome_proprio(_texto(dados.get("bairro"))), 60),
        "cidade": _cidade(db, dados),
        "telefones": list(dict.fromkeys(telefones)),
        "email": (_texto(dados.get("email")) or "").lower() or None,
        "fornecedor_id": existente.id if existente else None,
    }
