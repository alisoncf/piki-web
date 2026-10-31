import { flushPromises, mount } from '@vue/test-utils'
import { QLayout, QList, QPageContainer, Quasar } from 'quasar'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import ItemMenu from '@/componentes/ItemMenu.vue'
import InicioPagina from '@/paginas/InicioPagina.vue'
import { useSessaoStore } from '@/stores/sessao'
import { filtrarMenu, MENU, telasDoMenu } from '@/menu'

async function montar(caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:p(.*)*', component: vazio }] })
  await router.push(caminho)
  const menu = { render: () => h(QList, () => MENU.map((item) => h(ItemMenu, { item }))) }
  const wrapper = mount(menu, { global: { plugins: [Quasar, router] } })
  await flushPromises()
  return wrapper
}

describe('menu lateral', () => {
  it('abre só os grupos da página atual e marca o item', async () => {
    const wrapper = await montar('/cadastros/setores')
    const abertos = wrapper.findAll('.q-expansion-item--expanded').map((g) => g.find('.q-item__label').text())
    expect(abertos).toEqual(['Cadastros', 'Clientes']) // Funcionários e Acesso ficam fechados
    expect(wrapper.find('.piki-menu__ativo').text()).toContain('Setores')
  })

  it('a ficha marca a lista de onde veio', async () => {
    const wrapper = await montar('/cadastros/funcionarios/7')
    expect(wrapper.find('.piki-menu__ativo').text()).toContain('Funcionários')
  })
})

describe('atalhos da tela inicial', () => {
  it('são as telas liberadas dos subgrupos, com o caminho do grupo', () => {
    const telas = telasDoMenu(filtrarMenu(MENU, (p) => p === 'clientes.ver'))
    expect(telas.map((t) => [t.titulo, t.grupo, t.rota])).toEqual([
      ['Clientes', 'Cadastros › Clientes', '/cadastros/clientes'],
      ['Setores', 'Cadastros › Clientes', '/cadastros/setores'],
      ['Órgãos', 'Cadastros › Clientes', '/cadastros/orgaos'],
      ['Grupos', 'Cadastros › Clientes', '/cadastros/grupos-clientes'],
      ['Parentescos', 'Cadastros › Clientes', '/cadastros/parentescos'],
    ])
  })
  it('a tela inicial leva a cada tela liberada', async () => {
    setActivePinia(createPinia())
    const sessao = useSessaoStore()
    sessao.usuario = { nome: 'Bia Souza' }
    sessao.empresa = { id: 1, codigo: '01', nome: 'MATRIZ' }
    sessao.permissoes = ['funcionarios.ver']
    const vazio = { render: () => h('div') }
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/:p(.*)*', component: vazio }] })
    await router.push('/')
    const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(InicioPagina))) }
    const wrapper = mount(casca, { global: { plugins: [Quasar, router] } })
    await flushPromises()
    const links = wrapper.findAll('a.piki-atalho')
    expect(links.map((a) => a.attributes('href'))).toEqual(['/cadastros/funcionarios', '/cadastros/cargos'])
    expect(links[1].text()).toContain('Cadastros › Funcionários')
  })
})
