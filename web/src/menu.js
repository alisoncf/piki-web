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
