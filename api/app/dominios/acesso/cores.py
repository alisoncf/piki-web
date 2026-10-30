"""Cor de identificação de cada empresa, para o funcionário saber em que loja está.

A paleta é fechada: cores que se distinguem entre si, do ameixa da marca e do
verde e vermelho de sucesso e erro. A empresa sem cor escolhida recebe uma pelo código.
"""

PALETA: dict[str, str] = {
    "azul": "#2f6fb0",
    "laranja": "#d9822b",
    "verde-azulado": "#1f8a80",
    "roxo": "#6a4fc0",
    "oliva": "#7a862c",
    "marrom": "#8c5a3c",
    "ciano": "#2593b8",
    "ardosia": "#55708a",
}

_NOMES = list(PALETA)


def cor_padrao(codigo: str) -> str:
    """Nome da cor automática: 01 → 1ª da paleta, 02 → 2ª..., voltando ao início depois da 8ª."""
    numero = int(codigo) - 1 if codigo.isdigit() and int(codigo) > 0 else sum(map(ord, codigo))
    return _NOMES[numero % len(_NOMES)]


def cor_hex(nome: str | None, codigo: str) -> str:
    return PALETA.get(nome or "", PALETA[cor_padrao(codigo)])
