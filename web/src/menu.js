/**
 * Menu principal. Cada item pode exigir uma permissão (mesmo código usado na
 * API, ver api/app/nucleo/permissoes.py); itens sem permissão somem, e grupos
 * que ficam vazios também.
 */
export const MENU = [
  { titulo: 'Início', icone: 'home', rota: '/' },
  {
    titulo: 'Cadastros',
    icone: 'folder_shared',
    filhos: [
      { titulo: 'Clientes', icone: 'people', rota: '/cadastros/clientes', permissao: 'clientes.ver' },
      { titulo: 'Setores', icone: 'map', rota: '/cadastros/setores', permissao: 'clientes.ver' },
      { titulo: 'Órgãos', icone: 'apartment', rota: '/cadastros/orgaos', permissao: 'clientes.ver' },
      { titulo: 'Grupos de clientes', icone: 'category', rota: '/cadastros/grupos-clientes', permissao: 'clientes.ver' },
      { titulo: 'Parentescos', icone: 'diversity_3', rota: '/cadastros/parentescos', permissao: 'clientes.ver' },
      { titulo: 'Funcionários', icone: 'badge', rota: '/cadastros/funcionarios', permissao: 'funcionarios.ver' },
      { titulo: 'Cargos', icone: 'work_outline', rota: '/cadastros/cargos', permissao: 'funcionarios.ver' },
    ],
  },
  {
    titulo: 'Acesso',
    icone: 'admin_panel_settings',
    filhos: [{ titulo: 'Usuários', icone: 'group', rota: '/acesso/usuarios', permissao: 'acesso.usuarios' }],
  },
]

export function filtrarMenu(itens, pode) {
  return itens
    .map((item) => (item.filhos ? { ...item, filhos: filtrarMenu(item.filhos, pode) } : item))
    .filter((item) => (item.filhos ? item.filhos.length > 0 : pode(item.permissao)))
}
