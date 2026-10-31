"""Consulta de CEP no ViaCEP (https://viacep.com.br), serviço público e gratuito, sem chave."""
import httpx

from app.config import configuracao


class CepIndisponivel(Exception):
    """O ViaCEP não respondeu ou respondeu algo inesperado."""


def consultar(cep: str, cliente: httpx.Client | None = None) -> dict | None:
    """Os dados do CEP (8 dígitos) como o ViaCEP devolve, ou None se o CEP não existe."""
    url = configuracao().viacep_url.format(cep=cep)
    try:
        if cliente is None:
            with httpx.Client(timeout=configuracao().viacep_segundos) as novo:
                resposta = novo.get(url)
        else:
            resposta = cliente.get(url)
        if resposta.status_code == 400:  # formato inválido
            return None
        resposta.raise_for_status()
        dados = resposta.json()
    except (httpx.HTTPError, ValueError) as e:
        raise CepIndisponivel(str(e)) from e
    if not isinstance(dados, dict):
        raise CepIndisponivel("resposta inesperada")
    # CEP com formato certo mas inexistente: {"erro": "true"} (ou true, nas versões antigas)
    if dados.get("erro") in (True, "true"):
        return None
    return dados
