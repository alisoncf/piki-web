import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QInput, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import CampoCep from '@/componentes/CampoCep.vue'
import EmpresaPagina from '@/paginas/acesso/EmpresaPagina.vue'
import EmpresasPagina from '@/paginas/acesso/EmpresasPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const ANAPOLIS = { id: 5, codigo_ibge: '5201108', nome: 'Anápolis', uf: 'GO' }
const TEMA = { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' }
const MATRIZ = {
  id: 1, codigo: '01', nome: 'MATRIZ', razao_social: 'EMPRESA FICTICIA LTDA', nome_fantasia: null, cnpj: '11222333000181',
  inscricao_estadual: null, inscricao_municipal: null, suframa: null, crt: '1', sped_perfil: 'A', sped_atividade: '1',
  cep: '75110010', logradouro: 'Rua Um', numero: '10', complemento: null, bairro: 'Jundiaí', cidade_id: 5, cidade: ANAPOLIS,
  telefone: null, email: null, ativa: true, tema: TEMA, imagens: [],
}

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/acesso/empresas', name: 'empresas', component: componente === EmpresasPagina ? componente : vazio },
      { path: '/acesso/empresas/nova', name: 'empresa-nova', component: componente },
      { path: '/acesso/empresas/:id', name: 'empresa', component: componente },
    ],
  })
  await router.push(caminho)
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}

function entrar() {
  const sessao = useSessaoStore()
  sessao.usuario = { nome: 'Caio' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = ['acesso.empresas']
  return sessao
}

function campo(wrapper, rotulo) {
  return wrapper.findAllComponents(QInput).find((c) => c.props('label') === rotulo)
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

describe('empresas', () => {
  it('lista com a cor, o CNPJ e a cidade', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: [MATRIZ, { ...MATRIZ, id: 3, codigo: '03', nome: 'LA VIVA', ativa: false }] })
    const { wrapper } = await montar(EmpresasPagina, '/acesso/empresas')
    expect(wrapper.text()).toContain('MATRIZ')
    expect(wrapper.text()).toContain('11.222.333/0001-81')
    expect(wrapper.text()).toContain('Anápolis - GO')
    expect(wrapper.text()).toContain('Desativada')
  })

  it('altera as cores, gera fundo e menu e atualiza a sessão', async () => {
    const sessao = entrar()
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/auth/eu' ? { usuario: sessao.usuario, empresa: MATRIZ, empresas: [MATRIZ], permissoes: sessao.permissoes } : MATRIZ }))
    const put = vi.spyOn(api, 'put').mockImplementation(async (_, corpo) => ({ data: { ...MATRIZ, ...corpo } }))
    const { wrapper } = await montar(EmpresaPagina, '/acesso/empresas/1')

    expect(wrapper.text()).not.toContain('Código *') // o código não muda depois de criado
    expect(wrapper.text()).toContain('Anápolis - GO')
    await campo(wrapper, 'Principal').vm.$emit('update:modelValue', '#941D70')
    await wrapper.findAll('button').find((b) => b.text().includes('Gerar fundo e menu')).trigger('click')
    expect(campo(wrapper, 'Fundo').props('modelValue')).toBe('#f6edf4')
    expect(wrapper.find('.previa').attributes('style')).toContain('background: rgb(246, 237, 244)')

    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/empresas/1', expect.objectContaining({
      nome: 'MATRIZ', cidade_id: 5, tema: { principal: '#941d70', fundo: '#f6edf4', menu: '#2e1b2b' },
    }))
    expect(api.get).toHaveBeenCalledWith('/auth/eu') // a empresa ativa ganha as cores novas
  })

  it('notas fiscais: mostra o certificado e salva o ambiente e o CSC, sem mostrar o token', async () => {
    entrar()
    const FISCAL = { ambiente: '2', certificado: { titular: 'CN=LOJA FICTICIA LTDA:11222333000181', validade: '2027-03-01T10:00:00', dias_para_vencer: 20 }, csc_id: null, tem_csc: false }
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/empresas/1/fiscal' ? FISCAL : MATRIZ }))
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: { ...FISCAL, ambiente: '1', csc_id: '000001', tem_csc: true } })
    const { wrapper } = await montar(EmpresaPagina, '/acesso/empresas/1')
    expect(wrapper.text()).toContain('LOJA FICTICIA LTDA')
    expect(wrapper.text()).toContain('Vence em 01/03/2027 (20 dias)')
    await campo(wrapper, 'Id do CSC').vm.$emit('update:modelValue', '000001')
    await campo(wrapper, 'Token do CSC').vm.$emit('update:modelValue', 'TOKEN-FICTICIO')
    wrapper.findAllComponents({ name: 'QBtnToggle' }).at(-1).vm.$emit('update:modelValue', '1')
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('Salvar ambiente e CSC')).trigger('click')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/empresas/1/fiscal', { ambiente: '1', csc_id: '000001', csc_token: 'TOKEN-FICTICIO' })
    expect(campo(wrapper, 'Token do CSC').props('modelValue')).toBe('') // não fica na tela
  })

  it('nova: envia o código; o CEP traz rua, bairro e cidade', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({
      data: { cep: '75110010', logradouro: 'Rua Amaro Pires', complemento: null, bairro: 'Jundiaí', cidade: ANAPOLIS, setor: null, sugestoes: [] },
    })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...MATRIZ, id: 9, codigo: '04' } })
    const { wrapper, router } = await montar(EmpresaPagina, '/acesso/empresas/nova')

    await campo(wrapper, 'Código *').vm.$emit('update:modelValue', '04')
    await campo(wrapper, 'Nome curto *').vm.$emit('update:modelValue', 'NOVA')
    const cep = wrapper.findComponent(CampoCep)
    cep.vm.$emit('update:modelValue', '75110010')
    await flushPromises()
    await cep.find('button').trigger('click')
    await flushPromises()
    expect(api.get).toHaveBeenCalledWith('/cep/75110010')
    expect([campo(wrapper, 'Logradouro').props('modelValue'), campo(wrapper, 'Bairro').props('modelValue')])
      .toEqual(['Rua Amaro Pires', 'Jundiaí'])
    expect(wrapper.text()).toContain('Anápolis - GO')

    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/empresas', expect.objectContaining({
      codigo: '04', nome: 'NOVA', logradouro: 'Rua Amaro Pires', bairro: 'Jundiaí', cidade_id: 5,
    }))
    expect(router.currentRoute.value.params.id).toBe('9')
  })

  it('envia o logo como arquivo', async () => {
    entrar()
    globalThis.URL.createObjectURL ??= () => ''
    globalThis.URL.revokeObjectURL ??= () => {}
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:logo')
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url.includes('/imagens/') ? new Blob() : MATRIZ }))
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: { ...MATRIZ, imagens: ['logo'] } })
    const { wrapper } = await montar(EmpresaPagina, '/acesso/empresas/1')
    expect(wrapper.text()).toContain('Sem imagem')

    const arquivo = new File([new Uint8Array([0x89, 0x50])], 'logo.png', { type: 'image/png' })
    const entrada = wrapper.find('input[type="file"]')
    Object.defineProperty(entrada.element, 'files', { value: [arquivo] })
    await entrada.trigger('change')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/empresas/1/imagens/logo', arquivo, { headers: { 'Content-Type': 'image/png' } })
    expect(api.get).toHaveBeenCalledWith('/empresas/1/imagens/logo', { responseType: 'blob' })
    expect(wrapper.find('img[alt="Logo"]').attributes('src')).toBe('blob:logo')
  })
})
