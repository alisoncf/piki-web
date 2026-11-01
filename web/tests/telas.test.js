import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import LoginPagina from '@/paginas/LoginPagina.vue'
import EscolherEmpresaPagina from '@/paginas/EscolherEmpresaPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

function montar(componente) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'inicio', component: { template: '<div>início</div>' } },
      { path: '/login', name: 'login', component: componente },
      { path: '/empresa', name: 'escolher-empresa', component: componente },
    ],
  })
  const wrapper = mount(componente, { global: { plugins: [Quasar, router] } })
  return { wrapper, router }
}

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('tela de login', () => {
  it('mostra o erro da API sem sair da tela', async () => {
    vi.spyOn(api, 'post').mockRejectedValue({ response: { status: 401, data: { detail: 'Usuário ou senha incorretos' } } })
    const { wrapper } = montar(LoginPagina)
    await wrapper.find('input[autocomplete="username"]').setValue('bia')
    await wrapper.find('input[autocomplete="current-password"]').setValue('errada')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('Usuário ou senha incorretos')
  })

  it('com várias empresas, vai para a escolha', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({
      data: {
        access_token: 't', usuario: { id: 1, login: 'bia', nome: 'Bia', administrador: false },
        empresa: null, empresas: [{ id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }, { id: 3, codigo: '03', nome: 'LA VIVA', tema: { principal: '#1f8a80', fundo: '#edf6f5', menu: '#1d2f2f' } }],
        ultima_empresa_id: null,
      },
    })
    const { wrapper, router } = montar(LoginPagina)
    const ir = vi.spyOn(router, 'push')
    await wrapper.find('input[autocomplete="username"]').setValue('bia')
    await wrapper.find('input[autocomplete="current-password"]').setValue('x')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(ir).toHaveBeenCalledWith(expect.objectContaining({ name: 'escolher-empresa' }))
  })
})

describe('escolha de empresa', () => {
  it('lista as empresas do usuário e marca a última usada', () => {
    const sessao = useSessaoStore()
    sessao.usuario = { nome: 'Bia Souza' }
    sessao.empresas = [{ id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }, { id: 3, codigo: '03', nome: 'LA VIVA', tema: { principal: '#1f8a80', fundo: '#edf6f5', menu: '#1d2f2f' } }]
    sessao.ultimaEmpresaId = 3
    const { wrapper } = montar(EscolherEmpresaPagina)
    expect(wrapper.text()).toContain('Olá, Bia')
    expect(wrapper.text()).toContain('MATRIZ')
    expect(wrapper.text()).toContain('LA VIVA')
    expect(wrapper.text()).toContain('Última usada')
  })
})
