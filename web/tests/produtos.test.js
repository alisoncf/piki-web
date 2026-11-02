import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QInput, QLayout, QPageContainer, Quasar, QToggle } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import ProdutoPagina from '@/paginas/cadastros/ProdutoPagina.vue'
import ProdutosPagina from '@/paginas/cadastros/ProdutosPagina.vue'
import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
import { api } from '@/servicos/api'
import { formatarCodigoProduto, formatarMoeda } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }
const SECOES = [{ id: 1, nome: 'Cama', ativo: true, subsecoes: [{ id: 5, nome: 'Jogo de cama', ativo: true }] }]
const SUBSECAO = { id: 5, nome: 'Jogo de cama', ativo: true, secao_id: 1, secao: { id: 1, nome: 'Cama' } }
const TECIDOS = { id: 4, nome: 'Tecidos Fictícios Ltda', nome_fantasia: 'Fictícia Têxtil', ativo: true }
const JOGO = {
  id: 9, codigo: 1234, nome: 'JOGO DE CAMA CASAL FICTICIO', subsecao_id: 5, subsecao: SUBSECAO, marca_id: null, marca: null,
  unidade: 'UN', fracionado: false, custo: '50.00', margem: '100.00', preco_venda: '119.90', preco_queima: null,
  ncm: '63023100', cest: null, origem: 0, observacao: null, ativo: true, codigos_barras: ['7891234567895'],
  fornecedores: [{ fornecedor_id: 4, codigo: 'TR-04', fornecedor: TECIDOS }], fotos: [],
  criado_em: '2026-11-02T10:00:00', atualizado_em: '2026-11-02T10:00:00',
}

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/cadastros/produtos', name: 'produtos', component: componente === ProdutosPagina ? componente : vazio },
      { path: '/cadastros/produtos/novo', name: 'produto-novo', component: componente },
      { path: '/cadastros/produtos/:id', name: 'produto', component: componente },
    ],
  })
  await router.push(caminho)
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}

function entrar(permissoes = ['produtos.ver', 'produtos.editar', 'produtos.precos']) {
  const sessao = useSessaoStore()
  sessao.usuario = { nome: 'Caio' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = permissoes
}

function campo(wrapper, rotulo) {
  return wrapper.findAllComponents(QInput).find((c) => c.props('label') === rotulo)
}

function respostas(extra = {}) {
  const dados = { '/secoes': SECOES, '/marcas': [], '/fornecedores': [TECIDOS], '/produtos/9': JOGO, ...extra }
  return vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: dados[url] }))
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

describe('formatos', () => {
  it('código com 8 dígitos e preço em reais', () => {
    expect(formatarCodigoProduto(1234)).toBe('00001234')
    expect(formatarMoeda('1234.5').replace(/\s/g, ' ')).toBe('R$ 1.234,50')
    expect(formatarMoeda(null)).toBe('')
  })
})

describe('produtos', () => {
  it('lista com código, seção, fornecedor e queima; a busca vai para a API', async () => {
    entrar()
    const resumo = { ...JOGO, fornecedor: 'Fictícia Têxtil', foto_id: null, preco_queima: '89.90' }
    const get = respostas({ '/produtos': { itens: [resumo], total: 1 } })
    const { wrapper } = await montar(ProdutosPagina, '/cadastros/produtos')
    const texto = wrapper.text().replace(/\s/g, ' ')
    expect(texto).toContain('00001234')
    expect(texto).toContain('Cama › Jogo de cama')
    expect(texto).toContain('Fictícia Têxtil')
    expect(texto).toContain('R$ 89,90')
    expect(texto).toContain('Queima')
    expect(get).toHaveBeenCalledWith('/produtos', { params: { limite: 20, deslocamento: 0, ativo: true } })

    vi.useFakeTimers()
    await wrapper.findAllComponents(QInput)[0].vm.$emit('update:modelValue', 'cama casal')
    vi.useRealTimers()
    await flushPromises()
    expect(get).toHaveBeenLastCalledWith('/produtos', { params: { limite: 20, deslocamento: 0, busca: 'cama casal', ativo: true } })
  })

  it('altera a ficha e manda códigos de barras e fornecedores', async () => {
    entrar()
    respostas()
    const put = vi.spyOn(api, 'put').mockImplementation(async (_, dados) => ({ data: { ...JOGO, ...dados, fornecedores: JOGO.fornecedores } }))
    const { wrapper } = await montar(ProdutoPagina, '/cadastros/produtos/9')
    expect(campo(wrapper, 'Código').props('modelValue')).toBe('00001234')
    expect(wrapper.text()).toContain('7891234567895')
    expect(campo(wrapper, 'Preço de venda').props('hint')).toContain('100,00') // 50 + 100%

    await campo(wrapper, 'Acrescentar código (leia com o leitor ou digite e tecle Enter)').vm.$emit('update:modelValue', '7890000000001')
    await wrapper.find('button[aria-label="Acrescentar código"]').trigger('click')
    await wrapper.findAllComponents(QToggle).find((t) => t.props('label') === 'Em queima').vm.$emit('update:modelValue', true)
    await campo(wrapper, 'Preço de queima').vm.$emit('update:modelValue', '89.90')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/produtos/9', expect.objectContaining({
      codigos_barras: ['7891234567895', '7890000000001'],
      preco_queima: '89.90',
      cest: null,
      fornecedores: [{ fornecedor_id: 4, codigo: 'TR-04', embalagem: 1 }],
    }))
  })

  it('sem produtos.precos, custo e preços ficam só para ver', async () => {
    entrar(['produtos.ver', 'produtos.editar'])
    respostas()
    const { wrapper } = await montar(ProdutoPagina, '/cadastros/produtos/9')
    expect(wrapper.text()).toContain('Você não tem permissão para mudar custo e preços')
    expect(campo(wrapper, 'Preço de venda').props('readonly')).toBe(true)
    expect(campo(wrapper, 'Nome *').props('readonly')).toBeFalsy()
  })

  it('novo produto: escolhe a subseção e vai para a ficha criada', async () => {
    entrar()
    respostas()
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...JOGO, id: 10, codigo: 1235 } })
    const { wrapper, router } = await montar(ProdutoPagina, '/cadastros/produtos/novo')
    expect(campo(wrapper, 'Código').props('modelValue')).toBe('Automático')
    expect(wrapper.text()).not.toContain('Fotos') // só depois de criado
    const subsecao = wrapper.findAllComponents(SelecaoBusca)[0] // a primeira é a da subseção
    expect(subsecao.props('opcoes')).toEqual([{ id: 5, nome: 'Cama › Jogo de cama' }])
    await subsecao.vm.$emit('update:modelValue', 5)
    await campo(wrapper, 'Nome *').vm.$emit('update:modelValue', 'TOALHA FICTICIA')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/produtos', expect.objectContaining({ nome: 'TOALHA FICTICIA', subsecao_id: 5, preco_queima: null }))
    expect(router.currentRoute.value.params.id).toBe('10')
  })
})

describe('estoque na ficha do produto', () => {
  const ESTOQUE = {
    produto_id: 9, quantidade: '-2.000', reservado: '3.000', disponivel: '-5.000',
    localizacao: 'Prateleira 2', cst_csosn: '102', cfop: '5102', aliquota_icms: null,
  }
  const MOVIMENTO = {
    id: 1, data_hora: '2026-11-02T10:00:00', tipo: 'importacao', descricao: 'Saldo do VB6', quantidade: '-2.000',
    reservado: '3.000', saldo: '-2.000', saldo_reservado: '3.000', documento: null, observacao: 'Importado do VB6', usuario: null,
  }

  it('mostra saldo, reservado e histórico da loja ativa e ajusta a quantidade', async () => {
    entrar(['produtos.ver', 'estoque.ver', 'estoque.ajustar'])
    respostas({ '/produtos/9/estoque': ESTOQUE, '/produtos/9/estoque/movimentos': { itens: [MOVIMENTO], total: 1 } })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...ESTOQUE, quantidade: '10.000', disponivel: '7.000' } })
    const { wrapper } = await montar(ProdutoPagina, '/cadastros/produtos/9')
    const texto = wrapper.text()
    expect(texto).toContain('Estoque em MATRIZ')
    expect(texto).toContain('Com representantes')
    expect(texto).toContain('Estoque negativo')
    expect(texto).toContain('Saldo do VB6')
    expect(campo(wrapper, 'Localização na loja').props('readonly')).toBe(true) // sem estoque.editar

    await wrapper.findAll('button').find((b) => b.text().includes('Ajustar quantidade')).trigger('click')
    await flushPromises()
    const dialogo = wrapper.findAllComponents(QInput)
    await dialogo.find((c) => c.props('label') === 'Quantidade certa *').vm.$emit('update:modelValue', '10')
    await dialogo.find((c) => c.props('label') === 'Motivo *').vm.$emit('update:modelValue', 'Contagem')
    expect(dialogo.find((c) => c.props('label') === 'Quantidade certa *').props('hint')).toContain('diferença +12')
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/produtos/9/estoque/ajuste', { quantidade: '10', motivo: 'Contagem' })
  })

  it('sem estoque.ver, a ficha não mostra o estoque', async () => {
    entrar(['produtos.ver'])
    respostas()
    const { wrapper } = await montar(ProdutoPagina, '/cadastros/produtos/9')
    expect(wrapper.text()).not.toContain('Estoque em')
  })
})

describe('cadastro pelo atalho da entrada de notas', () => {
  it('vem preenchido com os dados do item e volta para a nota ao salvar', async () => {
    entrar()
    respostas()
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...JOGO, id: 10 } })
    const caminho = '/cadastros/produtos/novo?nome=TAPETE%20FICTICIO&ncm=57050000&ean=7890000000017&fornecedor=4&codigo_fornecedor=TA-99&volta=%2Fcompras%2Fentradas%2F7'
    const vazio = { render: () => h('div') }
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/cadastros/produtos/novo', name: 'produto-novo', component: ProdutoPagina },
        { path: '/cadastros/produtos/:id', name: 'produto', component: ProdutoPagina },
        { path: '/cadastros/produtos', name: 'produtos', component: vazio },
        { path: '/compras/entradas/:id', name: 'entrada', component: vazio },
      ],
    })
    await router.push(caminho)
    const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
    const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
    await flushPromises()
    expect(campo(wrapper, 'Nome *').props('modelValue')).toBe('TAPETE FICTICIO')
    expect(wrapper.text()).toContain('7890000000017')
    await wrapper.findAllComponents(SelecaoBusca)[0].vm.$emit('update:modelValue', 5)
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/produtos', expect.objectContaining({
      nome: 'TAPETE FICTICIO', ncm: '57050000', codigos_barras: ['7890000000017'],
      fornecedores: [{ fornecedor_id: 4, codigo: 'TA-99', embalagem: 1 }],
    }))
    expect(router.currentRoute.value.fullPath).toBe('/compras/entradas/7')
  })
})
