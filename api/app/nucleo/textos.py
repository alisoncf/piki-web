"""Tratamento de textos digitados ou vindos de fora (Receita, ViaCEP, VB6)."""
import re

# ficam em minúsculas no meio do nome
_LIGACOES = {"de", "da", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos", "a", "o"}
# siglas de tipo de empresa, que continuam em maiúsculas
_SIGLAS = {"me", "epp", "eireli", "mei", "s/a", "s.a.", "s.a", "sa", "ltda.", "cia", "cia."}
_SIGLAS_FORMA = {"ltda.": "Ltda.", "cia": "Cia", "cia.": "Cia."}


def nome_proprio(texto: str | None) -> str | None:
    """Maiúscula só nas iniciais: "TECIDOS DA SILVA LTDA" → "Tecidos da Silva Ltda", "ABC EPP" → "Abc EPP".

    Só mexe em texto todo em maiúsculas (ou todo em minúsculas); o que já tem
    maiúsculas e minúsculas misturadas foi escrito assim de propósito.
    """
    if not texto or not texto.strip():
        return None
    texto = " ".join(texto.split())
    if texto != texto.upper() and texto != texto.lower():
        return texto
    palavras = []
    for i, palavra in enumerate(texto.lower().split(" ")):
        if palavra in _SIGLAS_FORMA:
            palavras.append(_SIGLAS_FORMA[palavra])
        elif palavra in _SIGLAS:
            palavras.append(palavra.upper())
        elif i > 0 and palavra in _LIGACOES:
            palavras.append(palavra)
        else:
            # a inicial de cada parte: "d'oeste" → "D'Oeste", "sul-americana" → "Sul-Americana"
            palavras.append(re.sub(r"(^|[-'/(])(\w)", lambda m: m.group(1) + m.group(2).upper(), palavra))
    return " ".join(palavras)
