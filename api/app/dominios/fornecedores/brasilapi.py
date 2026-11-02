"""Consulta de CNPJ na BrasilAPI (https://brasilapi.com.br), serviço público e gratuito, sem chave."""
import httpx

from app.config import configuracao


class CnpjIndisponivel(Exception):
    """A BrasilAPI não respondeu ou respondeu algo inesperado."""


def consultar(cnpj: str, cliente: httpx.Client | None = None) -> dict | None:
    """Os dados do CNPJ (14 dígitos) como a BrasilAPI devolve, ou None se a Receita não conhece o CNPJ."""
    url = configuracao().brasilapi_cnpj_url.format(cnpj=cnpj)
    try:
        if cliente is None:
            # sem User-Agent a BrasilAPI responde 429 (muitas requisições)
            with httpx.Client(timeout=configuracao().brasilapi_segundos, headers={"User-Agent": "piki-web"}) as novo:
                resposta = novo.get(url)
        else:
            resposta = cliente.get(url)
        if resposta.status_code in (400, 404):  # formato inválido ou CNPJ não encontrado
            return None
        resposta.raise_for_status()
        dados = resposta.json()
    except (httpx.HTTPError, ValueError) as e:
        raise CnpjIndisponivel(str(e)) from e
    if not isinstance(dados, dict):
        raise CnpjIndisponivel("resposta inesperada")
    return dados
