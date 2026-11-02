import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QCheckbox, QInput, QLayout, QPageContainer, QSelect, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import ReceberCrediarioPagina from '@/paginas/caixa/ReceberCrediarioPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }
const DINHEIRO = { id: 1, nome: 'Dinheiro', tipo: 'dinheiro', parcelas: 1, parcelas_sem_autorizacao: 1 }
const CREDIARIO = { id: 9, nome: 'Crediário', tipo: 'crediario', parcelas: 10, parcelas_sem_autorizacao: 6 }
const BAIRRO = { id: 2, codigo: '02', nome: 'Loja Bairro' }
const PARCELAS = {
  juros_ao_mes: '5.00',
  parcelas: [
    { id: 31, conta_id: 7, loja: BAIRRO, venda: null, documento: '02-0000777', origem: 'acerto', numero: 1, parcelas: 2, vencimento: '2026-10-13', valor: '300.00', aberto: '300.00', dias_atraso: 20, juros: '10.00' },
    { id: 32, conta_id: 7, loja: BAIRRO, venda: null, documento: '02-0000777', origem: 'acerto', numero: 2, parcelas: 2, vencimento: '2026-11-13', valor: '300.00', aberto: '300.00', dias_atraso: 0, juros: '0.00' },
  ],
}

async function montar() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/caixa/crediario', name: 'receber-crediario', component: ReceberCrediarioPagina },
      { path: '/caixa', name: 'caixa', component: { render: () => h('div') } },
    ],
  })
  await router.push('/caixa/crediario')
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
  localStorage.clear()
  const sessao = useSessaoStore()
  sessao.usuario = { nome: 'Ana Caixa' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = ['caixa.operar']
})

describe('receber crediário', () => {
  it('marca a parcela atrasada, cobra os juros sugeridos e recebe no caixa do computador', async () => {
    localStorage.setItem('piki.caixa', JSON.stringify({ empresa_id: 1, id: 5, nome: 'Cx Crediário' }))
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: {
        '/formas-pagamento': [DINHEIRO, CREDIARIO],
        '/caixas': [{ id: 5, nome: 'Cx Crediário', ativo: true, sessao: { id: 11 } }],
        '/crediario/clientes/8/parcelas': PARCELAS,
      }[url],
    }))
    const recebido = {
      id: 40, empresa: { id: 1, codigo: '01', nome: 'MATRIZ' }, cliente: { id: 8, nome: 'Freguesa Ficticia' }, total: '310.00', troco: '10.00',
      pagamentos: [{ forma_pagamento: { id: 1, nome: 'Dinheiro', tipo: 'dinheiro' }, valor: '310.00' }], estornado_em: null, estornado_por: null,
    }
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: recebido })
    const wrapper = await montar()
    expect(wrapper.text()).toContain('Cx Crediário')

    await wrapper.findComponent(QSelect).vm.$emit('update:modelValue', 8)
    await flushPromises()
    expect(wrapper.text()).toContain('20 dias de atraso')
    expect(wrapper.text()).toContain('02-0000777 Acerto')
    expect(wrapper.text()).toContain('Juros sugeridos: 5% ao mês')

    await wrapper.findAllComponents(QCheckbox)[0].vm.$emit('update:modelValue', true)
    await flushPromises()
    expect(wrapper.text()).toMatch(/Total\s*R\$\s310,00/)
    await wrapper.findAll('button').find((b) => b.text().includes('Lançar pagamento')).trigger('click')
    await flushPromises()
    const recebidoDoCliente = wrapper.findAllComponents(QInput).find((c) => c.props('label')?.startsWith('Valor que o cliente deu'))
    await recebidoDoCliente.vm.$emit('update:modelValue', '320')
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('Confirmar recebimento')).trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/crediario/recebimentos', {
      sessao_caixa_id: 11, cliente_id: 8, valor_recebido: '320.00',
      itens: [{ parcela_id: 31, valor: '300.00', juros: '10.00' }],
      pagamentos: [{ forma_pagamento_id: 1, valor: '310.00' }],
    })
    expect(wrapper.text()).toContain('Recebimento 40')
    expect(wrapper.findAll('button').some((b) => b.text().includes('Estornar'))).toBe(true)
  })
})
