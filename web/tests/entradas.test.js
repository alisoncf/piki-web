import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QBtn, QInput, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import EntradaPagina from '@/paginas/compras/EntradaPagina.vue'
import EntradasPagina from '@/paginas/compras/EntradasPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }
const FORNECEDOR = { id: 4, nome: 'Tecidos Fictícios Ltda', nome_fantasia: 'Fictícia Têxtil', cpf_cnpj: '11222333000181' }
const PRODUTO = { id: 9, codigo: 1234, nome: 'JOGO DE CAMA FICTICIO', unidade: 'UN', fracionado: false, custo: '20.00', margem: '100.00', preco_venda: '59.90' }
const ITEM = {
  id: 1, numero: 1, codigo: 'JC-01', ean: null, descricao: 'JOGO DE CAMA FICT', ncm: '63023100', cest: null, cfop: '6102',
  unidade: 'CX', quantidade: '2.0000', valor_unitario: '120.000000', valor_produtos: '240.00', valor_custo: '272.00',
  embalagem: 1, unidades: '2.0000', custo_unitario: '136.00', preco_venda: null, produto: PRODUTO,
}
const NOTA = {
  id: 7, chave: '35261111222333000181550010000012341000012345', numero: 1234, serie: 1, data_emissao: '2026-10-30T09:15:00',
  valor_total: '999.99', situacao: 'aberta', fornecedor: FORNECEDOR, criado_em: '2026-11-02T10:00:00', confirmada_em: null,
  usuario: { id: 1, nome: 'Caio' }, confirmada_por: null, fornecedor_novo: false,
  itens: [ITEM, { ...ITEM, id: 2, numero: 2, codigo: 'TA-99', descricao: 'TAPETE NOVO FICTICIO', ean: '7890000000017', produto: null }],
}

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/compras/entradas', name: 'entradas', component: componente === EntradasPagina ? componente : vazio },
      { path: '/compras/entradas/:id', name: 'entrada', component: componente === EntradaPagina ? componente : vazio },
      { path: '/cadastros/produtos/novo', name: 'produto-novo', component: vazio },
      { path: '/cadastros/fornecedores/:id', name: 'fornecedor', component: vazio },
    ],
  })
  await router.push(caminho)
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}

function entrar(permissoes = ['entradas.ver', 'entradas.lancar', 'produtos.editar', 'produtos.precos']) {
  const sessao = useSessaoStore()
  sessao.usuario = { nome: 'Caio' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = permissoes
}

function botao(wrapper, texto) {
  return wrapper.findAllComponents(QBtn).find((b) => b.text().includes(texto))
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

describe('lista de notas', () => {
  it('carrega o XML e abre a nota; a repetida abre a que já existe', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: { itens: [NOTA], total: 1 } })
    const { wrapper, router } = await montar(EntradasPagina, '/compras/entradas')
    expect(wrapper.text()).toContain('Fictícia Têxtil')
    expect(wrapper.text()).toContain('1234/1')

    const xml = new File(['<nfeProc/>'], 'nota.xml', { type: 'text/xml' })
    const post = vi.spyOn(api, 'post').mockResolvedValueOnce({ data: NOTA })
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [xml], configurable: true })
    await input.trigger('change')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/entradas', xml, { headers: { 'Content-Type': 'application/xml' } })
    expect(router.currentRoute.value.params.id).toBe('7')

    await router.push('/compras/entradas')
    await flushPromises()
    post.mockRejectedValueOnce({ response: { status: 409, headers: { 'x-nota-id': '5' }, data: { detail: 'Esta nota já foi carregada' } } })
    const outro = wrapper.find('input[type="file"]')
    Object.defineProperty(outro.element, 'files', { value: [xml], configurable: true })
    await outro.trigger('change')
    await flushPromises()
    expect(router.currentRoute.value.params.id).toBe('5')
  })
})

describe('nota de entrada', () => {
  it('mostra o que falta ligar e não deixa confirmar antes', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: NOTA })
    const { wrapper } = await montar(EntradaPagina, '/compras/entradas/7')
    expect(wrapper.text()).toContain('1 de 2 itens ligados a produtos')
    expect(wrapper.text()).toContain('Não cadastrado')
    expect(wrapper.text()).toContain('00001234 · JOGO DE CAMA FICTICIO')
    expect(botao(wrapper, 'Confirmar entrada').props('disable')).toBe(true)
  })

  it('o atalho abre o cadastro do produto com os dados do item e volta para a nota', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: NOTA })
    const { wrapper, router } = await montar(EntradaPagina, '/compras/entradas/7')
    await botao(wrapper, 'Cadastrar produto').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('produto-novo')
    expect(router.currentRoute.value.query).toEqual({
      nome: 'TAPETE NOVO FICTICIO', ncm: '63023100', ean: '7890000000017', fornecedor: '4', codigo_fornecedor: 'TA-99',
      volta: '/compras/entradas/7',
    })
  })

  it('a embalagem e o preço novo vão para a API', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: NOTA })
    const put = vi.spyOn(api, 'put').mockImplementation(async (_, dados) => ({ data: { ...ITEM, ...dados, produto: PRODUTO } }))
    const { wrapper } = await montar(EntradaPagina, '/compras/entradas/7')
    const embalagem = wrapper.findAllComponents(QInput).find((c) => c.props('label') === 'Unidades por CX')
    await embalagem.vm.$emit('change', '6')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/entradas/7/itens/1', { produto_id: 9, embalagem: 6, preco_venda: null })
    await wrapper.find('button[aria-label="Usar o preço pela margem"]').trigger('click')
    await flushPromises()
    expect(put).toHaveBeenLastCalledWith('/entradas/7/itens/1', { produto_id: 9, embalagem: 6, preco_venda: '272.00' }) // 136 + 100%
  })
})
