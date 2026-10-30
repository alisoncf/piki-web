"""Importa os modelos de todos os domínios, para o Alembic e os testes enxergarem todas as tabelas.

Ao criar um domínio novo com tabelas, acrescente o import aqui.
"""
from app.dominios.acesso import modelos as acesso  # noqa: F401
from app.dominios.clientes import modelos as clientes  # noqa: F401
from app.dominios.funcionarios import modelos as funcionarios  # noqa: F401
from app.nucleo import legado  # noqa: F401
from app.nucleo.banco import Base  # noqa: F401
