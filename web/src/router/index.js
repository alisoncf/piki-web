import { Notify } from 'quasar'
import { createRouter, createWebHistory } from 'vue-router'

import { configurarApi } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

export const rotas = [
  { path: '/login', name: 'login', component: () => import('@/paginas/LoginPagina.vue'), meta: { publica: true } },
  { path: '/empresa', name: 'escolher-empresa', component: () => import('@/paginas/EscolherEmpresaPagina.vue') },
  {
    path: '/',
    component: () => import('@/layouts/PrincipalLayout.vue'),
    children: [
      { path: '', name: 'inicio', component: () => import('@/paginas/InicioPagina.vue') },
      {
        path: 'acesso/empresas',
        name: 'empresas',
        component: () => import('@/paginas/acesso/EmpresasPagina.vue'),
        meta: { permissao: 'acesso.empresas' },
      },
      {
        path: 'acesso/empresas/nova',
        name: 'empresa-nova',
        component: () => import('@/paginas/acesso/EmpresaPagina.vue'),
        meta: { permissao: 'acesso.empresas' },
      },
      {
        path: 'acesso/empresas/:id(\\d+)',
        name: 'empresa',
        component: () => import('@/paginas/acesso/EmpresaPagina.vue'),
        meta: { permissao: 'acesso.empresas' },
      },
      {
        path: 'acesso/usuarios',
        name: 'usuarios',
        component: () => import('@/paginas/acesso/UsuariosPagina.vue'),
        meta: { permissao: 'acesso.usuarios' },
      },
      {
        path: 'cadastros/clientes',
        name: 'clientes',
        component: () => import('@/paginas/cadastros/ClientesPagina.vue'),
        meta: { permissao: 'clientes.ver' },
      },
      {
        path: 'cadastros/clientes/novo',
        name: 'cliente-novo',
        component: () => import('@/paginas/cadastros/ClientePagina.vue'),
        meta: { permissao: 'clientes.editar' },
      },
      {
        path: 'cadastros/clientes/:id(\\d+)',
        name: 'cliente',
        component: () => import('@/paginas/cadastros/ClientePagina.vue'),
        meta: { permissao: 'clientes.ver' },
      },
      {
        path: 'cadastros/setores',
        name: 'setores',
        component: () => import('@/paginas/cadastros/SetoresPagina.vue'),
        meta: { permissao: 'clientes.ver' },
      },
      {
        path: 'cadastros/orgaos',
        name: 'orgaos',
        component: () => import('@/paginas/cadastros/OrgaosPagina.vue'),
        meta: { permissao: 'clientes.ver' },
      },
      {
        path: 'cadastros/grupos-clientes',
        name: 'grupos-clientes',
        component: () => import('@/paginas/cadastros/GruposClientesPagina.vue'),
        meta: { permissao: 'clientes.ver' },
      },
      {
        path: 'cadastros/parentescos',
        name: 'parentescos',
        component: () => import('@/paginas/cadastros/ParentescosPagina.vue'),
        meta: { permissao: 'clientes.ver' },
      },
      {
        path: 'cadastros/funcionarios',
        name: 'funcionarios',
        component: () => import('@/paginas/cadastros/FuncionariosPagina.vue'),
        meta: { permissao: 'funcionarios.ver' },
      },
      {
        path: 'cadastros/funcionarios/novo',
        name: 'funcionario-novo',
        component: () => import('@/paginas/cadastros/FuncionarioPagina.vue'),
        meta: { permissao: 'funcionarios.editar' },
      },
      {
        path: 'cadastros/funcionarios/:id(\\d+)',
        name: 'funcionario',
        component: () => import('@/paginas/cadastros/FuncionarioPagina.vue'),
        meta: { permissao: 'funcionarios.ver' },
      },
      {
        path: 'cadastros/fornecedores',
        name: 'fornecedores',
        component: () => import('@/paginas/cadastros/FornecedoresPagina.vue'),
        meta: { permissao: 'fornecedores.ver' },
      },
      {
        path: 'cadastros/fornecedores/novo',
        name: 'fornecedor-novo',
        component: () => import('@/paginas/cadastros/FornecedorPagina.vue'),
        meta: { permissao: 'fornecedores.editar' },
      },
      {
        path: 'cadastros/fornecedores/:id(\\d+)',
        name: 'fornecedor',
        component: () => import('@/paginas/cadastros/FornecedorPagina.vue'),
        meta: { permissao: 'fornecedores.ver' },
      },
      {
        path: 'cadastros/cargos',
        name: 'cargos',
        component: () => import('@/paginas/cadastros/CargosPagina.vue'),
        meta: { permissao: 'funcionarios.ver' },
      },
    ],
  },
  { path: '/:caminho(.*)*', name: 'nao-encontrada', component: () => import('@/paginas/NaoEncontradaPagina.vue'), meta: { publica: true } },
]

/** Para onde a navegação deve ir, ou true para seguir. Separado para poder testar. */
export function destino(para, sessao) {
  if (para.name === 'nao-encontrada') return true
  if (para.meta.publica) return sessao.logado ? { name: 'inicio' } : true
  if (!sessao.logado) return { name: 'login', query: para.fullPath !== '/' ? { volta: para.fullPath } : {} }
  if (sessao.precisaEscolherEmpresa) return para.name === 'escolher-empresa' ? true : { name: 'escolher-empresa' }
  if (para.meta.permissao && !sessao.pode(para.meta.permissao)) return { name: 'inicio' }
  return true
}

export function criarRoteador() {
  const roteador = createRouter({ history: createWebHistory(), routes: rotas })

  roteador.beforeEach(async (para) => {
    const sessao = useSessaoStore()
    await sessao.restaurar()
    const resultado = destino(para, sessao)
    if (resultado !== true && para.meta.permissao && sessao.logado && !sessao.precisaEscolherEmpresa) {
      Notify.create({ type: 'warning', message: 'Você não tem permissão para esta tela nesta empresa.' })
    }
    return resultado
  })

  configurarApi({
    aoPerderLogin: () => {
      useSessaoStore().sair()
      Notify.create({ type: 'info', message: 'Sua sessão terminou. Entre de novo.' })
      roteador.push({ name: 'login' })
    },
    aoPedirEmpresa: () => roteador.push({ name: 'escolher-empresa' }),
  })

  return roteador
}
