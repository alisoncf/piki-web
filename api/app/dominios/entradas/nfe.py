"""Leitura do XML da NF-e (layout 4.00) de entrada: o que a entrada de notas usa.

Aceita o XML autorizado (nfeProc, com o protocolo) ou só a NFe. Valores vêm
como Decimal, do jeito que estão no XML.
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.nucleo.documentos import so_digitos

_NS = "{http://www.portalfiscal.inf.br/nfe}"
ZERO = Decimal(0)


class XmlInvalido(Exception):
    """O arquivo não é o XML de uma NF-e."""


@dataclass
class Emitente:
    cpf_cnpj: str
    nome: str
    nome_fantasia: str | None
    inscricao_estadual: str | None
    cep: str | None
    logradouro: str | None
    numero: str | None
    complemento: str | None
    bairro: str | None
    codigo_municipio: str | None
    telefone: str | None


@dataclass
class Item:
    numero: int
    codigo: str  # cProd: o código do produto para o fornecedor
    ean: str | None  # cEAN ou cEANTrib, quando é um código de barras de verdade
    descricao: str
    ncm: str | None
    cest: str | None
    cfop: str | None
    unidade: str
    quantidade: Decimal
    valor_unitario: Decimal
    valor_produtos: Decimal
    valor_desconto: Decimal = ZERO
    valor_frete: Decimal = ZERO
    valor_seguro: Decimal = ZERO
    valor_outras: Decimal = ZERO
    valor_ipi: Decimal = ZERO
    valor_st: Decimal = ZERO  # ICMS ST e FCP ST


@dataclass
class Nota:
    chave: str
    numero: int
    serie: int
    data_emissao: datetime
    emitente: Emitente
    destinatario_cpf_cnpj: str
    valor_total: Decimal
    itens: list[Item] = field(default_factory=list)


def _filho(no: ET.Element | None, caminho: str) -> ET.Element | None:
    if no is None:
        return None
    return no.find("/".join(f"{_NS}{p}" for p in caminho.split("/")))


def _texto(no: ET.Element | None, caminho: str) -> str | None:
    alvo = _filho(no, caminho)
    if alvo is None or alvo.text is None:
        return None
    return " ".join(alvo.text.split()) or None


def _valor(no: ET.Element | None, caminho: str) -> Decimal:
    texto = _texto(no, caminho)
    try:
        return Decimal(texto) if texto else ZERO
    except InvalidOperation as e:
        raise XmlInvalido(f"Valor inválido em {caminho}: {texto}") from e


def _ean(*valores: str | None) -> str | None:
    """O primeiro código de barras de verdade ("SEM GTIN" e vazios ficam de fora)."""
    for v in valores:
        digitos = so_digitos(v)
        if 8 <= len(digitos) <= 14 and digitos == (v or "").strip():
            return digitos
    return None


def _imposto(imposto: ET.Element | None, tag: str) -> Decimal:
    """Soma a tag em qualquer grupo do imposto (ICMS00, ICMS10, ICMSSN202...)."""
    if imposto is None:
        return ZERO
    return sum((Decimal(no.text) for no in imposto.iter(f"{_NS}{tag}") if no.text), ZERO)


def ler(conteudo: bytes) -> Nota:
    # o expat do Python já barra a "bomba de entidades"; DTD numa NF-e não existe, então é recusado de saída
    if b"<!DOCTYPE" in conteudo[:2000].upper() or b"<!ENTITY" in conteudo.upper():
        raise XmlInvalido("O arquivo não é o XML de uma NF-e")
    try:
        raiz = ET.fromstring(conteudo)
    except ET.ParseError as e:
        raise XmlInvalido("O arquivo não é um XML válido") from e
    inf = raiz.find(f".//{_NS}infNFe")
    if inf is None:
        raise XmlInvalido("O arquivo não é o XML de uma NF-e")
    if _texto(inf, "ide/mod") not in (None, "55"):
        raise XmlInvalido("Só NF-e (modelo 55) dá entrada")
    chave = so_digitos(inf.get("Id"))
    if len(chave) != 44:
        raise XmlInvalido("Chave de acesso inválida no XML")

    emit = _filho(inf, "emit")
    endereco = _filho(emit, "enderEmit")
    emitente = Emitente(
        cpf_cnpj=so_digitos(_texto(emit, "CNPJ") or _texto(emit, "CPF")),
        nome=_texto(emit, "xNome") or "",
        nome_fantasia=_texto(emit, "xFant"),
        inscricao_estadual=so_digitos(_texto(emit, "IE")) or None,
        cep=so_digitos(_texto(endereco, "CEP")) or None,
        logradouro=_texto(endereco, "xLgr"),
        numero=_texto(endereco, "nro"),
        complemento=_texto(endereco, "xCpl"),
        bairro=_texto(endereco, "xBairro"),
        codigo_municipio=_texto(endereco, "cMun"),
        telefone=so_digitos(_texto(endereco, "fone")) or None,
    )
    emissao = _texto(inf, "ide/dhEmi") or _texto(inf, "ide/dEmi") or ""
    try:
        data_emissao = datetime.fromisoformat(emissao).replace(tzinfo=None)
    except ValueError as e:
        raise XmlInvalido("Data de emissão inválida no XML") from e

    nota = Nota(
        chave=chave,
        numero=int(_texto(inf, "ide/nNF") or 0),
        serie=int(_texto(inf, "ide/serie") or 0),
        data_emissao=data_emissao,
        emitente=emitente,
        destinatario_cpf_cnpj=so_digitos(_texto(inf, "dest/CNPJ") or _texto(inf, "dest/CPF")),
        valor_total=_valor(inf, "total/ICMSTot/vNF"),
    )
    for det in inf.findall(f"{_NS}det"):
        prod = _filho(det, "prod")
        imposto = _filho(det, "imposto")
        nota.itens.append(Item(
            numero=int(det.get("nItem") or len(nota.itens) + 1),
            codigo=_texto(prod, "cProd") or "",
            ean=_ean(_texto(prod, "cEAN"), _texto(prod, "cEANTrib")),
            descricao=_texto(prod, "xProd") or "",
            ncm=so_digitos(_texto(prod, "NCM")) or None,
            cest=so_digitos(_texto(prod, "CEST")) or None,
            cfop=_texto(prod, "CFOP"),
            unidade=(_texto(prod, "uCom") or "UN").upper()[:6],
            quantidade=_valor(prod, "qCom"),
            valor_unitario=_valor(prod, "vUnCom"),
            valor_produtos=_valor(prod, "vProd"),
            valor_desconto=_valor(prod, "vDesc"),
            valor_frete=_valor(prod, "vFrete"),
            valor_seguro=_valor(prod, "vSeg"),
            valor_outras=_valor(prod, "vOutro"),
            valor_ipi=_imposto(_filho(imposto, "IPI"), "vIPI"),
            valor_st=_imposto(_filho(imposto, "ICMS"), "vICMSST") + _imposto(_filho(imposto, "ICMS"), "vFCPST"),
        ))
    if not nota.itens:
        raise XmlInvalido("A nota não tem itens")
    return nota
