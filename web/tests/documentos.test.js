import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QLayout, QPageContainer, QSelect, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import DocumentosCliente from '@/componentes/DocumentosCliente.vue'
import ClientePagina from '@/paginas/cadastros/ClientePagina.vue'
import { api } from '@/servicos/api'
import { formatarTamanho } from '@/servicos/formatos'
import { reduzirImagem } from '@/servicos/imagens'
import { useSessaoStore } from '@/stores/sessao'

vi.mock('@/servicos/imagens', () => ({ reduzirImagem: vi.fn() }))

const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }
const RG = {
  id: 3, tipo: 'identidade', descricao: 'frente', nome_arquivo: 'rg.jpg', tipo_conteudo: 'image/jpeg', tamanho: 300000,
  data_hora: '2026-11-01T09:30:00', empresa: MATRIZ, usuario: { id: 1, nome: 'Bia' },
}
const CONTA = { ...RG, id: 4, tipo: 'endereco', descricao: null, nome_arquivo: 'conta.pdf', tipo_conteudo: 'application/pdf' }
const FICHA = {
  id: 7, nome: 'Maria Teste', tipo: 'F', cpf_cnpj: null, telefones: [], referencias: [], anotacoes: [], limite_credito: '0.00',
  data_cadastro: '2010-01-01', data_alteracao: null, empresa_cadastro: null, setor: null, setor_trabalho: null, grupo: null, orgao: null,
}

function entrar(permissoes) {
  const sessao = useSessaoStore()
  sessao.usuario = { nome: 'Bia' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = permissoes
}

function montarComponente(props = {}) {
  return mount(DocumentosCliente, {
    props: { clienteId: 7, ...props },
    global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }]] },
    attachTo: document.body,
  })
}

function botao(texto) {
  return [...document.querySelectorAll('button')].filter((b) => b.textContent.trim().endsWith(texto)).at(-1)
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
  globalThis.URL.createObjectURL ??= () => ''
  globalThis.URL.revokeObjectURL ??= () => {}
  vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:doc')
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
})

describe('documentos do cliente', () => {
  it('lista com miniatura das imagens e ícone dos PDFs', async () => {
    const get = vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url.endsWith('/arquivo') ? new Blob() : [RG, CONTA] }))
    const wrapper = montarComponente()
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/clientes/7/documentos')
    expect(get).toHaveBeenCalledWith('/clientes/7/documentos/3/arquivo', { responseType: 'blob' })
    expect(get).not.toHaveBeenCalledWith('/clientes/7/documentos/4/arquivo', expect.anything()) // PDF fica com ícone
    expect(wrapper.text()).toContain('Identidade (RG ou CNH)')
    expect(wrapper.text()).toContain('frente')
    expect(wrapper.text()).toContain('Comprovante de endereço')
    expect(wrapper.text()).toContain('01/11/2026 09:30 · Bia · MATRIZ')
    expect(wrapper.find('img').attributes('src')).toBe('blob:doc')
  })

  it('envia a foto reduzida, com o tipo e a descrição', async () => {
    vi.spyOn(api, 'get').mockResolvedValue({ data: [] })
    const reduzida = new File(['x'], 'foto.jpg', { type: 'image/jpeg' })
    reduzirImagem.mockResolvedValue(reduzida)
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...RG, id: 9 } })
    const wrapper = montarComponente()
    await flushPromises()
    expect(wrapper.text()).toContain('Nenhum documento.')

    const original = new File(['xxxx'], 'foto.png', { type: 'image/png' })
    const camera = wrapper.find('input[capture="environment"]')
    Object.defineProperty(camera.element, 'files', { value: [original] })
    await camera.trigger('change')
    await flushPromises()
    wrapper.findComponent(QSelect).vm.$emit('update:modelValue', 'identidade')
    await flushPromises()
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()

    expect(reduzirImagem).toHaveBeenCalledWith(original)
    expect(post).toHaveBeenCalledWith('/clientes/7/documentos', reduzida, {
      params: { tipo: 'identidade', descricao: undefined, nome: 'foto.jpg' },
      headers: { 'Content-Type': 'image/jpeg' },
    })
    expect(wrapper.text()).toContain('Identidade (RG ou CNH)')
  })

  it('abre o documento; remover só com permissão de editar', async () => {
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url.endsWith('/arquivo') ? new Blob() : [CONTA] }))
    const apagar = vi.spyOn(api, 'delete').mockResolvedValue({})
    const wrapper = montarComponente({ podeRemover: true })
    await flushPromises()

    await wrapper.find('.documento').trigger('click')
    await flushPromises()
    expect(document.querySelector('iframe').getAttribute('src')).toBe('blob:doc')
    expect(document.body.textContent).toContain('conta.pdf · 293 KB')
    botao('Remover').click()
    await flushPromises()
    botao('Remover').click() // o da confirmação
    await flushPromises()
    expect(apagar).toHaveBeenCalledWith('/clientes/7/documentos/4')
    expect(wrapper.text()).toContain('Nenhum documento.')
  })

  it.each([
    [['clientes.ver', 'clientes.editar'], false],
    [['clientes.ver', 'clientes.documentos'], true],
  ])('na ficha, só com clientes.documentos (LGPD): %j', async (permissoes, mostra) => {
    entrar(permissoes)
    const get = vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/clientes/7' ? FICHA : [] }))
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/cadastros/clientes/:id', name: 'cliente', component: ClientePagina }, { path: '/', name: 'clientes', component: { render: () => h('div') } }],
    })
    await router.push('/cadastros/clientes/7')
    const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
    const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] } })
    await flushPromises()
    expect(wrapper.text()).toContain('Anotações')
    expect(wrapper.text().includes('Documentos')).toBe(mostra)
    expect(get.mock.calls.some(([url]) => url === '/clientes/7/documentos')).toBe(mostra)
  })

  it('formata o tamanho', () => {
    expect(formatarTamanho(300)).toBe('1 KB')
    expect(formatarTamanho(300000)).toBe('293 KB')
    expect(formatarTamanho(1500000)).toBe('1,4 MB')
  })
})
