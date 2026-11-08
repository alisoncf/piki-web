import { Notify } from 'quasar'
import { createRouter, createWebHistory } from 'vue-router'

import { configurarApi } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

export const rotas = [
  { path: '/login', name: 'login', component: () => import('@/paginas/LoginPagina.vue'), meta: { publica: true } },
  { path: '/empresa', name: 'escolher-empresa', component: () => import('@/paginas/EscolherEmpresaPagina.vue') },
  { path: '/senha', name: 'trocar-senha', component: () => import('@/paginas/TrocarSenhaPagina.vue') },
  {
    // fora do layout, para imprimir só o canhoto
    path: '/vendas/:id(\\d+)/entrega',
    name: 'canhoto-entrega',
    component: () => import('@/paginas/vendas/CanhotoEntregaPagina.vue'),
    meta: { permissao: ['vendas.ver', 'vendas.vender', 'caixa.operar'] },
  },
  {
    // fora do layout, para imprimir só o DANFE na bobina
    path: '/vendas/:id(\\d+)/nota',
    name: 'nota-venda',
    component: () => import('@/paginas/notas/NotaVendaPagina.vue'),
    meta: { permissao: ['notas.ver', 'notas.emitir', 'caixa.operar'] },
  },
  {
    // fora do layout, para imprimir só o comprovante
    path: '/consignacao/transferencias/:id(\\d+)/comprovante',
    name: 'comprovante-transferencia',
    component: () => import('@/paginas/consignacao/ComprovanteConsignadoPagina.vue'),
    meta: { permissao: ['consignacao.transferir', 'representantes.ver'] },
  },
  {
    path: '/consignacao/devolucoes/:id(\\d+)/comprovante',
    name: 'comprovante-devolucao',
    component: () => import('@/paginas/consignacao/ComprovanteConsignadoPagina.vue'),
    meta: { permissao: ['consignacao.transferir', 'representantes.ver'] },
  },
  {
    path: '/consignacao/comissoes/pagamentos/:id(\\d+)',
    name: 'comprovante-comissao',
    component: () => import('@/paginas/consignacao/ComprovanteComissaoPagina.vue'),
    meta: { permissao: ['consignacao.comissoes', 'consignacao.pagar_comissao'] },
  },
  {
    path: '/consignacao/acertos/:id(\\d+)/comprovante',
    name: 'comprovante-acerto',
    component: () => import('@/paginas/consignacao/ComprovanteAcertoPagina.vue'),
    meta: { permissao: ['consignacao.acertar', 'representantes.ver'] },
  },
  {
    path: '/consignacao/acertos/:id(\\d+)/carne',
    name: 'carne-acerto',
    component: () => import('@/paginas/vendas/CarnePagina.vue'),
    meta: { permissao: ['consignacao.acertar', 'representantes.ver'] },
  },
  {
    // fora do layout, para imprimir só o carnê
    path: '/vendas/:id(\\d+)/carne',
    name: 'carne',
    component: () => import('@/paginas/vendas/CarnePagina.vue'),
    meta: { permissao: ['vendas.ver', 'vendas.vender', 'caixa.operar'] },
  },
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
        path: 'acesso/usuarios/novo',
        name: 'usuario-novo',
        component: () => import('@/paginas/acesso/UsuarioPagina.vue'),
        meta: { permissao: 'acesso.usuarios' },
      },
      {
        path: 'acesso/usuarios/:id(\\d+)',
        name: 'usuario',
        component: () => import('@/paginas/acesso/UsuarioPagina.vue'),
        meta: { permissao: 'acesso.usuarios' },
      },
      {
        path: 'acesso/perfis',
        name: 'perfis',
        component: () => import('@/paginas/acesso/PerfisPagina.vue'),
        meta: { permissao: 'acesso.perfis' },
      },
      {
        path: 'acesso/perfis/novo',
        name: 'perfil-novo',
        component: () => import('@/paginas/acesso/PerfilPagina.vue'),
        meta: { permissao: 'acesso.perfis' },
      },
      {
        path: 'acesso/perfis/:id(\\d+)',
        name: 'perfil',
        component: () => import('@/paginas/acesso/PerfilPagina.vue'),
        meta: { permissao: 'acesso.perfis' },
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
        path: 'cadastros/produtos',
        name: 'produtos',
        component: () => import('@/paginas/cadastros/ProdutosPagina.vue'),
        meta: { permissao: 'produtos.ver' },
      },
      {
        path: 'cadastros/produtos/novo',
        name: 'produto-novo',
        component: () => import('@/paginas/cadastros/ProdutoPagina.vue'),
        meta: { permissao: 'produtos.editar' },
      },
      {
        path: 'cadastros/produtos/:id(\\d+)',
        name: 'produto',
        component: () => import('@/paginas/cadastros/ProdutoPagina.vue'),
        meta: { permissao: 'produtos.ver' },
      },
      {
        path: 'cadastros/secoes',
        name: 'secoes',
        component: () => import('@/paginas/cadastros/SecoesPagina.vue'),
        meta: { permissao: 'produtos.ver' },
      },
      {
        path: 'cadastros/marcas',
        name: 'marcas',
        component: () => import('@/paginas/cadastros/MarcasPagina.vue'),
        meta: { permissao: 'produtos.ver' },
      },
      {
        path: 'compras/entradas',
        name: 'entradas',
        component: () => import('@/paginas/compras/EntradasPagina.vue'),
        meta: { permissao: 'entradas.ver' },
      },
      {
        path: 'compras/entradas/:id(\\d+)',
        name: 'entrada',
        component: () => import('@/paginas/compras/EntradaPagina.vue'),
        meta: { permissao: 'entradas.ver' },
      },
      {
        path: 'vendas',
        name: 'vendas',
        component: () => import('@/paginas/vendas/VendasPagina.vue'),
        meta: { permissao: ['vendas.ver', 'vendas.vender', 'caixa.operar'] },
      },
      {
        path: 'vendas/:id(\\d+)',
        name: 'venda',
        component: () => import('@/paginas/vendas/VendaPagina.vue'),
        meta: { permissao: ['vendas.ver', 'vendas.vender', 'caixa.operar'] },
      },
      {
        path: 'vendas/:id(\\d+)/receber',
        name: 'receber-venda',
        component: () => import('@/paginas/vendas/RecebimentoPagina.vue'),
        meta: { permissao: 'caixa.operar' },
      },
      {
        path: 'consignacao/representantes',
        name: 'representantes',
        component: () => import('@/paginas/consignacao/RepresentantesPagina.vue'),
        meta: { permissao: ['representantes.ver', 'representantes.editar', 'consignacao.transferir'] },
      },
      {
        path: 'consignacao/representantes/:id(\\d+)',
        name: 'representante',
        component: () => import('@/paginas/consignacao/RepresentantePagina.vue'),
        meta: { permissao: ['representantes.ver', 'representantes.editar', 'consignacao.transferir'] },
      },
      {
        path: 'consignacao/transferencias',
        name: 'transferencias',
        component: () => import('@/paginas/consignacao/TransferenciasPagina.vue'),
        meta: { permissao: ['consignacao.transferir', 'consignacao.acertar', 'representantes.ver'] },
      },
      {
        path: 'consignacao/transferencias/nova',
        name: 'transferencia-nova',
        component: () => import('@/paginas/consignacao/TransferenciaPagina.vue'),
        meta: { permissao: 'consignacao.transferir' },
      },
      {
        path: 'consignacao/transferencias/:id(\\d+)',
        name: 'transferencia',
        component: () => import('@/paginas/consignacao/TransferenciaPagina.vue'),
        meta: { permissao: 'consignacao.transferir' },
      },
      {
        path: 'consignacao/comissoes',
        name: 'comissoes',
        component: () => import('@/paginas/consignacao/ComissoesPagina.vue'),
        meta: { permissao: ['consignacao.comissoes', 'consignacao.pagar_comissao'] },
      },
      {
        path: 'consignacao/acertos/novo',
        name: 'acerto-novo',
        component: () => import('@/paginas/consignacao/AcertoPagina.vue'),
        meta: { permissao: 'consignacao.acertar' },
      },
      {
        path: 'consignacao/acertos/:id(\\d+)',
        name: 'acerto',
        component: () => import('@/paginas/consignacao/AcertoPagina.vue'),
        meta: { permissao: 'consignacao.acertar' },
      },
      {
        path: 'consignacao/devolucoes/nova',
        name: 'devolucao-nova',
        component: () => import('@/paginas/consignacao/DevolucaoPagina.vue'),
        meta: { permissao: 'consignacao.transferir' },
      },
      {
        path: 'consignacao/devolucoes/:id(\\d+)',
        name: 'devolucao',
        component: () => import('@/paginas/consignacao/DevolucaoPagina.vue'),
        meta: { permissao: 'consignacao.transferir' },
      },
      {
        path: 'notas/operacoes',
        name: 'operacoes-nota',
        component: () => import('@/paginas/notas/OperacoesNotaPagina.vue'),
        meta: { permissao: ['notas.configurar', 'notas.ver'] },
      },
      {
        path: 'notas/inutilizar',
        name: 'inutilizar-numeros',
        component: () => import('@/paginas/notas/InutilizarNumerosPagina.vue'),
        meta: { permissao: 'notas.inutilizar' },
      },
      {
        path: 'notas',
        name: 'notas',
        component: () => import('@/paginas/notas/NotasPagina.vue'),
        meta: { permissao: ['notas.ver', 'notas.emitir', 'caixa.operar'] },
      },
      {
        path: 'caixa',
        name: 'caixa',
        component: () => import('@/paginas/caixa/CaixaPagina.vue'),
        meta: { permissao: ['caixa.operar', 'caixa.conferir'] },
      },
      {
        path: 'caixa/sessoes/:id(\\d+)',
        name: 'sessao-caixa',
        component: () => import('@/paginas/caixa/SessaoCaixaPagina.vue'),
        meta: { permissao: ['caixa.operar', 'caixa.conferir'] },
      },
      {
        path: 'financeiro/receber',
        name: 'contas-receber',
        component: () => import('@/paginas/financeiro/ContasReceberPagina.vue'),
        meta: { permissao: 'receber.ver' },
      },
      {
        path: 'financeiro/plano-contas',
        name: 'plano-contas',
        component: () => import('@/paginas/financeiro/PlanoContasPagina.vue'),
        meta: { permissao: 'financeiro.plano' },
      },
      {
        path: 'financeiro/contas-cobranca',
        name: 'contas-cobranca',
        component: () => import('@/paginas/financeiro/ContasCobrancaPagina.vue'),
        meta: { permissao: ['receber.ver', 'receber.cobranca'] },
      },
      {
        path: 'caixa/crediario',
        name: 'receber-crediario',
        component: () => import('@/paginas/caixa/ReceberCrediarioPagina.vue'),
        meta: { permissao: 'caixa.operar' },
      },
      {
        path: 'caixa/formas',
        name: 'formas-pagamento',
        component: () => import('@/paginas/caixa/FormasPagamentoPagina.vue'),
        meta: { permissao: 'caixa.configurar' },
      },
      {
        path: 'caixa/caixas',
        name: 'caixas',
        component: () => import('@/paginas/caixa/CaixasPagina.vue'),
        meta: { permissao: 'caixa.configurar' },
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
  if (sessao.precisaTrocarSenha) {
    return para.name === 'trocar-senha' ? true : { name: 'trocar-senha', query: para.fullPath !== '/' ? { volta: para.fullPath } : {} }
  }
  if (para.name === 'trocar-senha') return true
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
