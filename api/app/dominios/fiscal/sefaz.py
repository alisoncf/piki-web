"""Conversa com a SEFAZ de Goiás (D29), pela nfelib: assinar, autorizar, consultar e cancelar.

Fica num lugar só para os testes trocarem pelo falso (não há SEFAZ nos testes), e para o
resto do sistema não depender da nfelib. Toda resposta vira um Retorno simples.
"""
from dataclasses import dataclass
from datetime import datetime

from app.dominios.fiscal.nfce import NS, UF_GO

# os códigos de resposta da SEFAZ (cStat) que importam aqui
AUTORIZADA = "100"
AUTORIZADA_FORA_DO_PRAZO = "150"
CANCELADA = "101"
CANCELADA_FORA_DO_PRAZO = "151"
DENEGADAS = {"110", "301", "302", "303"}
DUPLICIDADE = "204"  # já autorizada antes: a resposta da primeira vez se perdeu
EM_PROCESSAMENTO = "105"
EVENTO_REGISTRADO = {"135", "136", "155"}
INUTILIZACAO_HOMOLOGADA = "102"
SERVICO_EM_OPERACAO = "107"


class SemConexao(Exception):
    """A SEFAZ não respondeu (fora do ar, sem internet, tempo esgotado)."""


@dataclass
class Retorno:
    codigo: str
    motivo: str
    protocolo: str | None = None
    recebido_em: datetime | None = None
    xml_protocolo: str | None = None  # o protNFe ou o retEvento, para guardar com a nota


def _trecho(resposta, tag: str) -> str | None:
    """O elemento como veio da SEFAZ (o protNFe, o retEvento), sem passar pela nfelib: é o que se guarda."""
    from lxml import etree

    elemento = etree.fromstring(resposta.retorno.content).find(f".//{{{NS}}}{tag}")
    return None if elemento is None else etree.tostring(elemento, encoding="unicode")


def _data(texto: str | None) -> datetime | None:
    if not texto:
        return None
    return datetime.fromisoformat(str(texto)).replace(tzinfo=None)


def _do_protocolo(resposta) -> Retorno:
    info = resposta.resposta.protNFe.infProt
    return Retorno(str(info.cStat), info.xMotivo, info.nProt, _data(info.dhRecbto), _trecho(resposta, "protNFe"))


def assinar(xml: str, pfx: bytes, senha: str, chave: str) -> str:
    from nfelib import CommonMixin

    return CommonMixin.sign_xml(xml, pfx, senha, f"NFe{chave}")


def erros_de_leiaute(xml: str) -> list[str]:
    """Confere o XML com o esquema oficial (XSD) antes de mandar: a rejeição sai na hora, sem gastar ida à SEFAZ."""
    from nfelib.nfe.bindings.v4_0.nfe_v4_00 import Nfe

    return Nfe.schema_validation(xml)


def com_protocolo(xml_assinado: str, xml_protocolo: str) -> str:
    """O nfeProc: a nota assinada, intacta, mais o protocolo de autorização. É o XML que vale."""
    nota = xml_assinado.split("?>", 1)[-1].strip()
    return f'<?xml version="1.0" encoding="UTF-8"?><nfeProc versao="4.00" xmlns="{NS}">{nota}{xml_protocolo}</nfeProc>'


def _cliente_go(**kwargs):
    """O cliente da nfelib com o que a SEFAZ de Goiás pede: SOAP 1.2 (com SOAP 1.1 ela responde 415), e sem o
    cabeçalho vazio da resposta, que a nfelib não sabe ler."""
    import re

    from nfelib.nfe.client.v4_0.nfe import NfeClient

    class ClienteGo(NfeClient):
        def prepare_headers(self, headers: dict) -> dict:
            return {**super().prepare_headers(headers), "content-type": "application/soap+xml; charset=utf-8"}

        def _post(self, location: str, data: str, headers: dict) -> bytes:
            return re.sub(rb"<(\w+:)?Header\s*/>", b"", super()._post(location, data, headers))

    return ClienteGo(soap12_envelope=True, **kwargs)


class Sefaz:
    def __init__(self, ambiente: str, pfx: bytes, senha: str, timeout: float = 30):
        self._cliente = _cliente_go(ambiente=ambiente, uf=UF_GO, pkcs12_data=pfx, pkcs12_password=senha, mod="65",
                                    timeout=timeout, wrap_response=True)

    def _chamar(self, funcao, *args, **kwargs):
        import requests

        try:
            return funcao(*args, **kwargs)
        except requests.RequestException as e:
            raise SemConexao(f"A SEFAZ não respondeu ({e.__class__.__name__}): tente de novo em instantes") from e

    def status(self) -> Retorno:
        r = self._chamar(self._cliente.status_servico).resposta
        return Retorno(str(r.cStat), r.xMotivo)

    def autorizar(self, xml_assinado: str) -> Retorno:
        """Envio síncrono (NFC-e): a resposta já traz o protocolo da nota."""
        from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TenviNfeIndSinc

        lote = datetime.now().strftime("%Y%m%d%H%M%S")
        resposta = self._chamar(self._cliente.envia_documento, [xml_assinado], lote, TenviNfeIndSinc.VALUE_1)
        r = resposta.resposta
        if r.protNFe is not None:
            return _do_protocolo(resposta)
        return Retorno(str(r.cStat), r.xMotivo)  # o lote foi recusado inteiro (ou ficou em processamento)

    def consultar(self, chave: str) -> Retorno:
        resposta = self._chamar(self._cliente.consulta_documento, chave)
        r = resposta.resposta
        if r.protNFe is not None:
            retorno = _do_protocolo(resposta)
            retorno.codigo = str(r.cStat)  # 101 se já foi cancelada; o protocolo é o da autorização
            return retorno
        return Retorno(str(r.cStat), r.xMotivo)

    def cancelar(self, chave: str, protocolo: str, justificativa: str, cnpj: str) -> Retorno:
        evento = self._cliente.cancela_documento(chave, protocolo, justificativa, cnpj,
                                                 datetime.now().strftime("%Y-%m-%dT%H:%M:%S-03:00"))
        resposta = self._chamar(self._cliente.enviar_lote_evento, [evento])
        r = resposta.resposta
        if not r.retEvento:
            return Retorno(str(r.cStat), r.xMotivo)
        ret = r.retEvento[0]
        info = ret.infEvento
        return Retorno(str(info.cStat), info.xMotivo, info.nProt, _data(info.dhRegEvento), _trecho(resposta, "retEvento"))

    def inutilizar(self, cnpj: str, modelo: str, serie: int, inicial: int, final: int, justificativa: str) -> Retorno:
        pedido = self._cliente.inutilizacao(cnpj, modelo, str(serie), str(inicial), str(final), justificativa)
        resposta = self._chamar(self._cliente.envia_inutilizacao, pedido)
        info = resposta.resposta.infInut
        return Retorno(str(info.cStat), info.xMotivo, info.nProt, _data(info.dhRecbto), _trecho(resposta, "retInutNFe"))
