"""Senhas no formato do VB6 (piki_Simples).

O legado guarda a senha em tab_usuarios.SENHA_USU com uma codificação
reversível, não com hash:

    F_GeraPW:    cada caractere vira ChrW(Asc(c) + 1 + posição)   (posição a partir de 1)
    F_RetornaPW: cada caractere vira ChrW(Asc(c) - 1 - posição)

No login, o VB6 passa o texto digitado por P_AjustaTexto (maiúsculas e troca
de alguns caracteres) e compara com a senha decodificada, também em
maiúsculas. Ou seja, a senha não diferencia maiúsculas de minúsculas.

Referências no legado: requinte/modulos/Modulo.bas (F_GeraPW, F_RetornaPW,
P_AjustaTexto) e requinte/forms/frmLogin.frm (cmndbtnEntr_Click).

Na importação (decisão D8), o ETL decodifica a senha e grava só o hash, com
usuario.senha_sem_caixa = True para continuar aceitando maiúsculas ou
minúsculas, como no VB6, até o usuário trocar a senha no sistema novo.
"""
from app.nucleo.seguranca import gerar_hash, normalizar_legado


def _asc(c: str) -> int:
    """Equivalente ao Asc() do VB6: código ANSI (cp1252) quando existe."""
    try:
        b = c.encode("cp1252")
        if len(b) == 1:
            return b[0]
    except UnicodeEncodeError:
        pass
    return ord(c)


def decodificar(armazenada: str) -> str:
    """Porta de F_RetornaPW."""
    return "".join(chr(_asc(c) - 1 - i) for i, c in enumerate(armazenada.rstrip(), start=1))


def codificar(senha: str) -> str:
    """Porta de F_GeraPW. Usado só nos testes, para montar dados no formato antigo."""
    return "".join(chr(_asc(c) + 1 + i) for i, c in enumerate(senha, start=1))


def conferir(digitada: str, armazenada: str | None) -> bool:
    """Confere a senha digitada contra o valor de SENHA_USU, como o VB6 faz."""
    if not armazenada:
        return False
    return decodificar(armazenada).upper() == normalizar_legado(digitada)


def hash_para_importar(armazenada: str | None) -> str | None:
    """Converte o SENHA_USU do legado no hash gravado em usuario.hash_senha."""
    if not armazenada or not armazenada.strip():
        return None
    return gerar_hash(decodificar(armazenada), sem_caixa=True)
