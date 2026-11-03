/**
 * Menu principal. Cada item pode exigir uma permissão, ou uma lista em que basta uma (mesmo código usado na
 * API, ver api/app/nucleo/permissoes.py); itens sem permissão somem, e grupos
 * que ficam vazios também. Grupos podem ter subgrupos, em qualquer nível.
 */
export const MENU = [
  { titulo: 'Início', icone: 'home', rota: '/' },
  {
    titulo: 'Cadastros',
    icone: 'folder_shared',
    filhos: [
      {
        titulo: 'Clientes',
        icone: 'people',
        filhos: [
          { titulo: 'Clientes', icone: 'people', rota: '/cadastros/clientes', permissao: 'clientes.ver' },
          { titulo: 'Setores', icone: 'map', rota: '/cadastros/setores', permissao: 'clientes.ver' },
          { titulo: 'Órgãos', icone: 'apartment', rota: '/cadastros/orgaos', permissao: 'clientes.ver' },
          { titulo: 'Grupos', icone: 'category', rota: '/cadastros/grupos-clientes', permissao: 'clientes.ver' },
          { titulo: 'Parentescos', icone: 'diversity_3', rota: '/cadastros/parentescos', permissao: 'clientes.ver' },
        ],
      },
      { titulo: 'Fornecedores', icone: 'local_shipping', rota: '/cadastros/fornecedores', permissao: 'fornecedores.ver' },
      {
        titulo: 'Produtos',
        icone: 'inventory_2',
        filhos: [
          { titulo: 'Produtos', icone: 'inventory_2', rota: '/cadastros/produtos', permissao: 'produtos.ver' },
          { titulo: 'Seções', icone: 'account_tree', rota: '/cadastros/secoes', permissao: 'produtos.ver' },
          { titulo: 'Marcas', icone: 'sell', rota: '/cadastros/marcas', permissao: 'produtos.ver' },
        ],
      },
      {
        titulo: 'Funcionários',
        icone: 'badge',
        filhos: [
          { titulo: 'Funcionários', icone: 'badge', rota: '/cadastros/funcionarios', permissao: 'funcionarios.ver' },
          { titulo: 'Cargos', icone: 'work_outline', rota: '/cadastros/cargos', permissao: 'funcionarios.ver' },
        ],
      },
    ],
  },
  {
    titulo: 'Vendas',
    icone: 'shopping_bag',
    filhos: [
      { titulo: 'Vendas', icone: 'shopping_bag', rota: '/vendas', permissao: ['vendas.ver', 'vendas.vender', 'caixa.operar'] },
      { titulo: 'Notas fiscais', icone: 'receipt_long', rota: '/notas', permissao: ['notas.ver', 'notas.emitir', 'caixa.operar'] },
      { titulo: 'Inutilizar números', icone: 'block', rota: '/notas/inutilizar', permissao: 'notas.inutilizar' },
    ],
  },
  {
    titulo: 'Caixa',
    icone: 'point_of_sale',
    filhos: [
      { titulo: 'Caixa', icone: 'point_of_sale', rota: '/caixa', permissao: ['caixa.operar', 'caixa.conferir'] },
      { titulo: 'Receber crediário', icone: 'request_quote', rota: '/caixa/crediario', permissao: 'caixa.operar' },
      { titulo: 'Formas de pagamento', icone: 'payments', rota: '/caixa/formas', permissao: 'caixa.configurar' },
      { titulo: 'Caixas da loja', icone: 'storefront', rota: '/caixa/caixas', permissao: 'caixa.configurar' },
    ],
  },
  {
    titulo: 'Financeiro',
    icone: 'account_balance',
    filhos: [
      { titulo: 'Contas a receber', icone: 'request_quote', rota: '/financeiro/receber', permissao: 'receber.ver' },
      { titulo: 'Plano de contas', icone: 'account_tree', rota: '/financeiro/plano-contas', permissao: 'financeiro.plano' },
      { titulo: 'Contas de cobrança', icone: 'contact_mail', rota: '/financeiro/contas-cobranca', permissao: ['receber.ver', 'receber.cobranca'] },
    ],
  },
  {
    titulo: 'Compras',
    icone: 'shopping_cart',
    filhos: [
      { titulo: 'Entrada de notas', icone: 'receipt_long', rota: '/compras/entradas', permissao: 'entradas.ver' },
    ],
  },
  {
    titulo: 'Acesso',
    icone: 'admin_panel_settings',
    filhos: [
      { titulo: 'Empresas', icone: 'store', rota: '/acesso/empresas', permissao: 'acesso.empresas' },
      { titulo: 'Usuários', icone: 'group', rota: '/acesso/usuarios', permissao: 'acesso.usuarios' },
      { titulo: 'Perfis', icone: 'admin_panel_settings', rota: '/acesso/perfis', permissao: 'acesso.perfis' },
    ],
  },
]

export function filtrarMenu(itens, pode) {
  return itens
    .map((item) => (item.filhos ? { ...item, filhos: filtrarMenu(item.filhos, pode) } : item))
    .filter((item) => (item.filhos ? item.filhos.length > 0 : pode(item.permissao)))
}

/** Se a página atual é deste item ou de um dos seus filhos (a ficha /cadastros/clientes/7 é de Clientes). */
export function contemRota(item, caminho) {
  if (item.filhos) return item.filhos.some((filho) => contemRota(filho, caminho))
  if (item.rota === '/') return caminho === '/'
  return caminho === item.rota || caminho.startsWith(`${item.rota}/`)
}

/**
 * As telas do menu, sem os grupos, cada uma com o caminho dos grupos onde está
 * ("Cadastros › Clientes"). São os atalhos da tela inicial.
 */
export function telasDoMenu(itens, grupos = []) {
  return itens.flatMap((item) => (item.filhos
    ? telasDoMenu(item.filhos, [...grupos, item.titulo])
    : [{ ...item, grupo: grupos.join(' › ') }]))
}
