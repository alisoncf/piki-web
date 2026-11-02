import { mount } from '@vue/test-utils'
import { Quasar } from 'quasar'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import IndiceFicha from '@/componentes/IndiceFicha.vue'

const SECOES = [{ id: 'secao-a', titulo: 'Identificação' }, { id: 'secao-b', titulo: 'Telefones' }, { id: 'secao-c', titulo: 'Endereço' }]

// posição de cada seção em relação ao topo da janela
function posicionar(topos) {
  for (const [id, top] of Object.entries(topos)) {
    document.getElementById(id).getBoundingClientRect = () => ({ top })
  }
}

function montar() {
  document.body.innerHTML = '<header class="q-header"></header><div id="secao-a"></div><div id="secao-b"></div><div id="secao-c"></div>'
  Object.defineProperty(document.querySelector('.q-header'), 'offsetHeight', { value: 55 })
  return mount(IndiceFicha, { props: { secoes: SECOES }, global: { plugins: [Quasar] }, attachTo: document.body })
}

function ativo(wrapper) {
  return wrapper.find('[aria-current="location"]').text()
}

beforeEach(() => vi.spyOn(window, 'scrollTo').mockImplementation(() => {}))
afterEach(() => vi.restoreAllMocks())

describe('índice da ficha', () => {
  it('fica preso logo abaixo do cabeçalho e começa na primeira seção', async () => {
    const wrapper = montar()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('nav').attributes('style')).toContain('top: 55px')
    expect(wrapper.findAll('button').map((b) => b.text())).toEqual(['Identificação', 'Telefones', 'Endereço'])
    expect(ativo(wrapper)).toBe('Identificação')
  })

  it('o clique rola a página até a seção, abaixo do cabeçalho e do índice', async () => {
    const wrapper = montar()
    posicionar({ 'secao-a': 100, 'secao-b': 700, 'secao-c': 1300 })
    await wrapper.findAll('button')[2].trigger('click')
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 1300 - 55 - 8, behavior: 'smooth' })
    expect(ativo(wrapper)).toBe('Endereço')
  })

  it('ao rolar, marca a última seção que passou do topo', async () => {
    const wrapper = montar()
    posicionar({ 'secao-a': -500, 'secao-b': 40, 'secao-c': 600 })
    window.dispatchEvent(new Event('scroll'))
    await wrapper.vm.$nextTick()
    expect(ativo(wrapper)).toBe('Telefones')
    wrapper.unmount()
  })
})
