"""CPF, telefone e outros dados de pessoa, comuns a funcionários, clientes e fornecedores."""
import re


def so_digitos(valor: object) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def cpf_valido(cpf: str) -> bool:
    """Confere os dígitos verificadores. Recebe só os 11 dígitos."""
    if len(cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d) * peso for d, peso in zip(cpf[:tamanho], range(tamanho + 1, 1, -1)))
        digito = (soma * 10) % 11 % 10
        if digito != int(cpf[tamanho]):
            return False
    return True


# tipos de telefone, com os mesmos códigos do VB6 (tab_telefones.tipo_tel)
TIPOS_TELEFONE: dict[str, str] = {
    "1": "Residencial",
    "2": "Comercial",
    "3": "Celular",
    "4": "Recado",
    "5": "Fax",
}


def cnpj_valido(cnpj: str) -> bool:
    """Confere os dígitos verificadores. Recebe só os 14 dígitos."""
    if len(cnpj) != 14 or not cnpj.isdigit() or cnpj == cnpj[0] * 14:
        return False
    for tamanho in (12, 13):
        pesos = list(range(tamanho - 7, 1, -1)) + list(range(9, 1, -1))
        soma = sum(int(d) * p for d, p in zip(cnpj[:tamanho], pesos))
        digito = 0 if soma % 11 < 2 else 11 - soma % 11
        if digito != int(cnpj[tamanho]):
            return False
    return True


def cpf_cnpj_valido(documento: str) -> bool:
    """CPF (11 dígitos) ou CNPJ (14 dígitos)."""
    return cpf_valido(documento) if len(documento) == 11 else cnpj_valido(documento)
