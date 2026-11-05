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
    "estoque.ver": "Consultar o estoque da loja e o histórico de movimentos",
    "estoque.editar": "Alterar a localização e os impostos do produto na loja",
    "estoque.ajustar": "Ajustar a quantidade em estoque da loja",
    "entradas.ver": "Consultar as notas de entrada da loja",
    "entradas.lancar": "Carregar o XML, ligar os itens aos produtos e confirmar a entrada das notas",
    "caixa.operar": "Abrir, lançar entradas e saídas e fechar o caixa (sem ver o saldo esperado)",
    "caixa.conferir": "Ver o saldo esperado do caixa e os fechamentos, com as diferenças",
    "caixa.configurar": "Cadastrar caixas da loja e formas de pagamento",
    "vendas.ver": "Consultar as vendas da loja",
    "vendas.vender": "Montar vendas no balcão, com desconto até o limite do perfil",
    "vendas.autorizar": "Autorizar parcelas acima do limite da forma de pagamento",
    "vendas.cancelar": "Cancelar venda já recebida, nos primeiros dias e sem parcela paga (desfaz caixa, estoque e carnê)",
    "financeiro.plano": "Cadastrar o plano de contas (as contas de receita e de despesa)",
    "receber.ver": "Consultar as contas a receber de todas as lojas, com os filtros e as somas",
    "receber.cobranca": "Mudar os carnês de conta de cobrança (cobrador, advogado...) e cadastrar as contas",
    "receber.editar": "Prorrogar parcelas (também em lote) e editar o tipo de cobrança e o cabeçalho dos documentos",
    "receber.prejuizo": "Pôr parcelas no prejuízo (não se espera mais receber) e tirar de lá",
    "notas.ver": "Consultar as notas fiscais emitidas pela loja (NFC-e e NF-e) e baixar o XML",
    "notas.emitir": "Emitir, transmitir de novo e consultar na SEFAZ as notas da loja (o caixa já emite a da venda)",
    "notas.cancelar": "Cancelar nota autorizada na SEFAZ",
    "notas.inutilizar": "Inutilizar na SEFAZ os números pulados das séries da loja",
    "representantes.ver": "Consultar os representantes (consignado)",
    "representantes.editar": "Cadastrar representantes, trocar a senha, o avalista e os lembretes",
    "representantes.limites": "Alterar o limite, o bloqueio e as comissões dos representantes",
    "consignacao.transferir": "Atender o representante no balcão do consignado: transferências e devoluções (e ver o que está com ele)",
    "consignacao.acertar": "Fazer o acerto do representante no caixa do consignado (para o cliente dele ou para ele)",
    "consignacao.liberar": "Liberar a devolução e a impressão do representante que tem esses bloqueios (o gerente)",
    "notas.configurar": "Alterar a natureza da operação e o CFOP das notas (venda, remessa, retorno, devolução)",
}

# nome de cada área (a parte antes do ponto), para agrupar as permissões na tela de perfis
AREAS: dict[str, str] = {
    "acesso": "Acesso",
    "funcionarios": "Funcionários",
    "clientes": "Clientes",
    "fornecedores": "Fornecedores",
    "produtos": "Produtos",
    "estoque": "Estoque",
    "entradas": "Entrada de notas",
    "caixa": "Caixa",
    "vendas": "Vendas",
    "receber": "Contas a receber",
    "financeiro": "Financeiro",
    "notas": "Notas fiscais",
    "representantes": "Representantes",
    "consignacao": "Consignação",
}
