"""Catálogo de permissões (decisão D10).

Cada permissão é um código `area.acao`. O catálogo vive no código: ao criar
uma tela nova, acrescente aqui as permissões dela e rode
`python -m app.cli sincronizar-permissoes` para gravá-las no banco.
"""

PERMISSOES: dict[str, str] = {
    "acesso.usuarios": "Ver e gerenciar usuários e seus acessos às empresas",
    "acesso.perfis": "Ver e gerenciar perfis e suas permissões",
    "acesso.empresas": "Ver e gerenciar o cadastro de empresas",
    "funcionarios.ver": "Consultar funcionários e cargos",
    "funcionarios.editar": "Cadastrar e alterar funcionários e cargos",
    "clientes.ver": "Consultar clientes, setores, órgãos e grupos de clientes",
    "clientes.editar": "Cadastrar e alterar clientes, setores, órgãos e grupos de clientes",
    "clientes.documentos": "Ver e enviar documentos dos clientes (crediário; dados pessoais protegidos pela LGPD)",
    "fornecedores.ver": "Consultar fornecedores",
    "fornecedores.editar": "Cadastrar e alterar fornecedores",
    "produtos.ver": "Consultar produtos, seções e marcas",
    "produtos.editar": "Cadastrar e alterar produtos, seções e marcas",
    "produtos.precos": "Alterar custo, margem e preços dos produtos",
}

# nome de cada área (a parte antes do ponto), para agrupar as permissões na tela de perfis
AREAS: dict[str, str] = {
    "acesso": "Acesso",
    "funcionarios": "Funcionários",
    "clientes": "Clientes",
    "fornecedores": "Fornecedores",
    "produtos": "Produtos",
}
