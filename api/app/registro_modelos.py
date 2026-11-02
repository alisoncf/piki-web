"""Importa os modelos de todos os domínios, para o Alembic e os testes enxergarem todas as tabelas.

Ao criar um domínio novo com tabelas, acrescente o import aqui.
"""
from app.dominios.acesso import modelos as acesso  # noqa: F401
from app.dominios.cidades import modelos as cidades  # noqa: F401
from app.dominios.clientes import modelos as clientes  # noqa: F401
from app.dominios.empresas import modelos as empresas  # noqa: F401
from app.dominios.entradas import modelos as entradas  # noqa: F401
from app.dominios.estoque import modelos as estoque  # noqa: F401
from app.dominios.fornecedores import modelos as fornecedores  # noqa: F401
from app.dominios.funcionarios import modelos as funcionarios  # noqa: F401
from app.dominios.produtos import modelos as produtos  # noqa: F401
from app.nucleo import legado  # noqa: F401
from app.nucleo.banco import Base  # noqa: F401
