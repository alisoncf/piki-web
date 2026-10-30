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
