"""Regras do cadastro de empresas."""
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives.serialization import pkcs12
from sqlalchemy.orm import Session

from app.config import configuracao
from app.dominios.cidades.modelos import Cidade
from app.dominios.empresas import repositorio as repo
from app.dominios.empresas.esquemas import EmpresaDados, EmpresaNova
from app.dominios.empresas.modelos import Empresa, ImagemEmpresa
from app.nucleo import segredos
from app.nucleo.documentos import cnpj_valido

TIPOS_DE_IMAGEM = {"logo": "Logo dos relatórios", "qrcode": "QR code do boleto de cobrança"}
TAMANHO_MAXIMO = 1024 * 1024  # 1 MB por imagem
# PNG e JPEG, reconhecidos pelo começo do arquivo (SVG fica de fora: pode levar script)
_ASSINATURAS = {b"\x89PNG\r\n\x1a\n": "image/png", b"\xff\xd8\xff": "image/jpeg"}


class ErroEmpresa(Exception):
    """Erro de regra do cadastro; a mensagem vai para o usuário."""


class NaoEncontrada(ErroEmpresa):
    pass


class DadoInvalido(ErroEmpresa):
    pass


class Duplicada(ErroEmpresa):
    pass


def obter_empresa(db: Session, empresa_id: int) -> Empresa:
    empresa = db.get(Empresa, empresa_id)
    if empresa is None:
        raise NaoEncontrada("Empresa não encontrada")
    return empresa


def _conferir(db: Session, dados: EmpresaDados, empresa_id: int | None) -> None:
    if dados.cnpj:
        if not cnpj_valido(dados.cnpj):
            raise DadoInvalido("CNPJ inválido")
        outra = repo.empresa_por_cnpj(db, dados.cnpj)
        if outra and outra.id != empresa_id:
            raise Duplicada(f"O CNPJ já é da empresa {outra.codigo} - {outra.nome}")
    if dados.cidade_id is not None and db.get(Cidade, dados.cidade_id) is None:
        raise DadoInvalido("Cidade não encontrada")


def _aplicar(empresa: Empresa, dados: EmpresaDados) -> None:
    for campo, valor in dados.model_dump(exclude={"tema", "codigo"}).items():
        setattr(empresa, campo, valor)
    empresa.tema = dados.tema.model_dump() if dados.tema else None


def criar_empresa(db: Session, dados: EmpresaNova) -> Empresa:
    if repo.empresa_por_codigo(db, dados.codigo):
        raise Duplicada(f"Já existe a empresa {dados.codigo}")
    _conferir(db, dados, None)
    empresa = Empresa(codigo=dados.codigo)
    _aplicar(empresa, dados)
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    return empresa


def alterar_empresa(db: Session, empresa_id: int, dados: EmpresaDados) -> Empresa:
    empresa = obter_empresa(db, empresa_id)
    _conferir(db, dados, empresa_id)
    _aplicar(empresa, dados)
    db.commit()
    db.refresh(empresa)
    return empresa


def _tipo(tipo: str) -> str:
    if tipo not in TIPOS_DE_IMAGEM:
        raise NaoEncontrada(f"Imagem desconhecida: {tipo}. Use {' ou '.join(TIPOS_DE_IMAGEM)}")
    return tipo


def obter_imagem(db: Session, empresa_id: int, tipo: str) -> ImagemEmpresa:
    imagem = repo.imagem(db, obter_empresa(db, empresa_id).id, _tipo(tipo))
    if imagem is None:
        raise NaoEncontrada(f"A empresa não tem {TIPOS_DE_IMAGEM[tipo].lower()}")
    return imagem


def gravar_imagem(db: Session, empresa_id: int, tipo: str, conteudo: bytes) -> Empresa:
    empresa = obter_empresa(db, empresa_id)
    _tipo(tipo)
    if len(conteudo) > TAMANHO_MAXIMO:
        raise DadoInvalido("A imagem passa de 1 MB")
    formato = next((f for inicio, f in _ASSINATURAS.items() if conteudo.startswith(inicio)), None)
    if formato is None:
        raise DadoInvalido("Envie uma imagem PNG ou JPEG")
    imagem = repo.imagem(db, empresa.id, tipo)
    if imagem is None:
        imagem = ImagemEmpresa(empresa_id=empresa.id, tipo=tipo)
        db.add(imagem)
    imagem.tipo_conteudo, imagem.conteudo = formato, conteudo
    db.commit()
    db.refresh(empresa)
    return empresa


def apagar_imagem(db: Session, empresa_id: int, tipo: str) -> Empresa:
    imagem = obter_imagem(db, empresa_id, tipo)
    empresa = imagem.empresa
    db.delete(imagem)
    db.commit()
    db.refresh(empresa)
    return empresa


# ------------------------------------------------------------ notas fiscais (D29)

def fiscal(empresa: Empresa) -> dict:
    certificado = None
    if empresa.certificado_arquivo:
        dias = (empresa.certificado_validade - datetime.now()).days if empresa.certificado_validade else None
        certificado = {"titular": empresa.certificado_titular, "validade": empresa.certificado_validade,
                       "dias_para_vencer": dias}
    return {"ambiente": empresa.nfe_ambiente, "certificado": certificado, "csc_id": empresa.csc_id,
            "csc_token": _decifrado(empresa.csc_token)}


def _decifrado(cifrado: str | None) -> str | None:
    """O token do CSC aparece na ficha (Alison, 03/11/2026); no banco continua cifrado. Sem a chave, não aparece."""
    if not cifrado:
        return None
    try:
        return segredos.decifrar(cifrado)
    except segredos.SemChave:
        return None


def configurar_fiscal(db: Session, empresa_id: int, ambiente: str, csc_id: str | None, csc_token: str | None) -> Empresa:
    empresa = obter_empresa(db, empresa_id)
    empresa.nfe_ambiente = ambiente
    empresa.csc_id = (csc_id or "").strip() or None
    if csc_token and csc_token.strip():
        empresa.csc_token = _cifrar(csc_token.strip())
    db.commit()
    return empresa


def _cifrar(texto: str) -> str:
    try:
        return segredos.cifrar(texto)
    except segredos.SemChave as e:
        raise DadoInvalido(str(e))


def gravar_certificado(db: Session, empresa_id: int, conteudo: bytes, senha: str) -> Empresa:
    """Confere o .pfx com a senha, guarda o arquivo na pasta dos certificados (fora do banco) e a senha cifrada.
    O certificado tem de ser do CNPJ da empresa."""
    empresa = obter_empresa(db, empresa_id)
    try:
        chave, cert, _ = pkcs12.load_key_and_certificates(conteudo, senha.encode())
    except ValueError:
        raise DadoInvalido("Não foi possível abrir o certificado: confira o arquivo e a senha")
    if chave is None or cert is None:
        raise DadoInvalido("O arquivo não tem o certificado com a chave")
    titular = cert.subject.rfc4514_string()
    if empresa.cnpj and empresa.cnpj not in "".join(ch for ch in titular if ch.isdigit()):
        raise DadoInvalido(f"O certificado não é do CNPJ da empresa ({titular})")
    validade = cert.not_valid_after_utc.replace(tzinfo=None)
    if validade < datetime.now():
        raise DadoInvalido(f"O certificado venceu em {validade:%d/%m/%Y}")
    senha_cifrada = _cifrar(senha)
    pasta = Path(configuracao().certificados_pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"{empresa.codigo}-{empresa.cnpj or empresa.id}.pfx"
    (pasta / nome).write_bytes(conteudo)
    empresa.certificado_arquivo, empresa.certificado_senha = nome, senha_cifrada
    empresa.certificado_titular, empresa.certificado_validade = titular[:200], validade
    db.commit()
    return empresa
