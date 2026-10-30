"""Identificação da filial (cod_emp) em cada requisição.

Ver decisão D3 em docs/decisoes.md: toda tabela de movimento é filtrada por
cod_emp. Por enquanto a filial vem do cabeçalho X-Cod-Emp; quando o login
existir, ela passa a vir do usuário autenticado.
"""
from typing import Annotated

from fastapi import Header, HTTPException

from app.config import configuracao


def cod_emp_atual(x_cod_emp: Annotated[str | None, Header()] = None) -> str:
    cod = x_cod_emp or configuracao().cod_emp_padrao
    if len(cod) != 2 or not cod.isdigit():
        raise HTTPException(status_code=400, detail="X-Cod-Emp deve ter 2 dígitos, por exemplo 01")
    return cod
