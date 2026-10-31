/**
 * Menu principal. Cada item pode exigir uma permissão (mesmo código usado na
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

/** Se a página atual é deste item ou de um dos seus filhos (a ficha /cadastros/clientes/7 é de Clientes). */
export function contemRota(item, caminho) {
  if (item.filhos) return item.filhos.some((filho) => contemRota(filho, caminho))
  if (item.rota === '/') return caminho === '/'
  return caminho === item.rota || caminho.startsWith(`${item.rota}/`)
}
