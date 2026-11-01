"""Esquema de cores de cada empresa, para o funcionário saber em que loja está (D19).

O administrador escolhe as três cores na ficha da empresa. A empresa que ainda
não tem esquema recebe um automático, a partir de uma cor da paleta pelo código.
A mesma conta de `tema_da_cor` está no front (web/src/servicos/tema.js), no
botão "Gerar a partir da cor principal".
"""

# cores principais para as empresas sem esquema: 01 → azul, 02 → laranja...
PALETA = ["#2f6fb0", "#d9822b", "#1f8a80", "#6a4fc0", "#7a862c", "#8c5a3c", "#2593b8", "#55708a"]

_BRANCO = "#ffffff"
_GRAFITE = "#1c1b1f"


def misturar(cor: str, outra: str, proporcao: float) -> str:
    """`proporcao` de `cor` com o resto de `outra` (como o color-mix do CSS, em sRGB)."""
    a = [int(cor[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(outra[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * proporcao + y * (1 - proporcao)):02x}" for x, y in zip(a, b))


def tema_da_cor(principal: str) -> dict[str, str]:
    """Fundo das telas bem claro e menu grafite, os dois puxados para a cor principal."""
    principal = principal.lower()
    return {"principal": principal, "fundo": misturar(principal, _BRANCO, 0.08), "menu": misturar(principal, _GRAFITE, 0.15)}


def tema_automatico(codigo: str) -> dict[str, str]:
    numero = int(codigo) - 1 if codigo.isdigit() and int(codigo) > 0 else sum(map(ord, codigo))
    return tema_da_cor(PALETA[numero % len(PALETA)])
