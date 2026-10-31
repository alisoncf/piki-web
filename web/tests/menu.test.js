import { flushPromises, mount } from '@vue/test-utils'
import { QList, Quasar } from 'quasar'
import { describe, expect, it } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import ItemMenu from '@/componentes/ItemMenu.vue'
import { MENU } from '@/menu'

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
