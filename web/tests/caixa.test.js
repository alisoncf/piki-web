import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QInput, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import CaixaPagina from '@/paginas/caixa/CaixaPagina.vue'
import SessaoCaixaPagina from '@/paginas/caixa/SessaoCaixaPagina.vue'
import { api } from '@/servicos/api'
import { useCaixaDaMaquinaStore } from '@/stores/caixaDaMaquina'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }
const DINHEIRO = { id: 1, nome: 'Dinheiro', tipo: 'dinheiro' }
const PIX = { id: 2, nome: 'PIX', tipo: 'pix' }
const ANA = { id: 3, nome: 'Ana Caixa' }
const SESSAO = { id: 11, situacao: 'aberto', fundo: '100.00', aberto_em: '2026-11-02T08:00:00', aberto_por: ANA, fechado_em: null, fechado_por: null }
const LANCAMENTO = {
  id: 1, data_hora: '2026-11-02T09:00:00', tipo: 'entrada', motivo: 'outra_entrada', descricao_motivo: 'Outra entrada',
  forma_pagamento: PIX, valor: '80.00', historico: 'Acerto', funcionario: null, documento: null, usuario: ANA,
  estornado_em: null, estornado_por: null,
}
const ABERTA = { ...SESSAO, caixa: { id: 5, nome: 'Cx 02' }, caixa_id: 5, observacao: null, lancamentos: [LANCAMENTO], totais: null, conferencia: [] }

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/caixa', name: 'caixa', component: componente === CaixaPagina ? componente : vazio },
      { path: '/caixa/sessoes/:id', name: 'sessao-caixa', component: componente === SessaoCaixaPagina ? componente : vazio },
    ],
  })
  await router.push(caminho)
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}

function entrar(permissoes = ['caixa.operar']) {
  const sessao = useSessaoStore()
  sessao.usuario = { nome: 'Ana Caixa' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = permissoes
  return sessao
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
  localStorage.clear()
})

describe('caixa', () => {
  it('permissão em lista: basta ter uma', () => {
    const sessao = entrar(['caixa.conferir'])
    expect(sessao.pode(['caixa.operar', 'caixa.conferir'])).toBe(true)
    expect(sessao.pode(['caixa.operar'])).toBe(false)
  })

  it('lista os caixas da loja e abre com o fundo de troco', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: [
      { id: 5, nome: 'Cx 02', ativo: true, sessao: SESSAO },
      { id: 6, nome: 'Cx 03', ativo: true, sessao: null },
      { id: 7, nome: 'Sem caixa', ativo: false, sessao: null },
    ] })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...ABERTA, id: 12 } })
    const { wrapper, router } = await montar(CaixaPagina, '/caixa')
    expect(wrapper.text()).toContain('Aberto por Ana Caixa')
    expect(wrapper.text()).not.toContain('Sem caixa') // desativado
    expect(wrapper.text()).not.toContain('Fechamentos') // só para quem confere

    await wrapper.findAll('button').find((b) => b.text().includes('Abrir')).trigger('click')
    await flushPromises()
    const fundo = wrapper.findAllComponents(QInput).find((c) => c.props('label') === 'Fundo de troco')
    await fundo.vm.$emit('update:modelValue', '150')
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/caixas/6/abrir', { fundo: '150' })
    expect(router.currentRoute.value.params.id).toBe('12')
    // quem abre deixa este computador no caixa
    expect(JSON.parse(localStorage.getItem('piki.caixa'))).toEqual({ empresa_id: 1, id: 6, nome: 'Cx 03' })
  })

  it('entrar num caixa aberto deixa o computador nele', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: [{ id: 5, nome: 'Cx 02', ativo: true, sessao: SESSAO }] })
    const { wrapper, router } = await montar(CaixaPagina, '/caixa')
    await wrapper.findAll('button').find((b) => b.text().includes('Entrar')).trigger('click')
    await flushPromises()
    expect(useCaixaDaMaquinaStore().caixa).toEqual({ empresa_id: 1, id: 5, nome: 'Cx 02' })
    expect(router.currentRoute.value.params.id).toBe('11')
    // noutra empresa, este computador não está em caixa nenhum
    useSessaoStore().empresa = { ...MATRIZ, id: 2 }
    expect(useCaixaDaMaquinaStore().caixa).toBeNull()
  })

  it('conferência cega: o operador não vê o saldo e conta dinheiro e as formas lançadas', async () => {
    entrar()
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/formas-pagamento' ? [DINHEIRO, PIX] : ABERTA }))
    const conferencia = [
      { forma_pagamento: DINHEIRO, esperado: '100.00', contado: '98.00', diferenca: '-2.00' },
      { forma_pagamento: PIX, esperado: '80.00', contado: '80.00', diferenca: '0.00' },
    ]
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...ABERTA, situacao: 'fechado', fechado_por: ANA, conferencia } })
    const { wrapper } = await montar(SessaoCaixaPagina, '/caixa/sessoes/11')
    expect(wrapper.text()).toContain('Outra entrada')
    expect(wrapper.text()).not.toContain('Saldo esperado')

    await wrapper.findAll('button').find((b) => b.text().includes('Fechar caixa')).trigger('click')
    await flushPromises()
    const contados = wrapper.findAllComponents(QInput).filter((c) => c.props('label')?.endsWith('contado'))
    expect(contados.map((c) => c.props('label'))).toEqual(['Dinheiro contado', 'PIX contado'])
    await contados[0].vm.$emit('update:modelValue', '98')
    await contados[1].vm.$emit('update:modelValue', '80')
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/caixas/sessoes/11/fechar', {
      contagem: [{ forma_pagamento_id: 1, contado: '98' }, { forma_pagamento_id: 2, contado: '80' }], observacao: null,
    })
    expect(wrapper.text()).toContain('Conferência do fechamento')
    expect(wrapper.text().replace(/\s/g, ' ')).toContain('-R$ 2,00')
  })

  it('o vale pede o funcionário', async () => {
    entrar()
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: { '/formas-pagamento': [DINHEIRO, PIX], '/funcionarios': [{ id: 9, nome: 'Laura Ficticia' }] }[url] ?? ABERTA,
    }))
    const post = vi.spyOn(api, 'post').mockImplementation(async (_, dados) => ({ data: { ...LANCAMENTO, id: 2, ...dados, tipo: 'saida' } }))
    const { wrapper } = await montar(SessaoCaixaPagina, '/caixa/sessoes/11')
    await wrapper.findAll('button').find((b) => b.text().includes('Saída')).trigger('click')
    await flushPromises()
    const dialogo = wrapper.findAllComponents(QInput)
    const motivo = wrapper.findAllComponents({ name: 'QSelect' }).find((c) => c.props('label') === 'Motivo *')
    await motivo.vm.$emit('update:modelValue', 'vale')
    await flushPromises()
    expect(document.body.textContent).toContain('Funcionário *')
    await dialogo.find((c) => c.props('label') === 'Valor *').vm.$emit('update:modelValue', '30')
    const funcionario = wrapper.findAllComponents({ name: 'SelecaoBusca' })[0]
    await funcionario.vm.$emit('update:modelValue', 9)
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/caixas/sessoes/11/lancamentos', {
      motivo: 'vale', valor: '30', forma_pagamento_id: 1, historico: null, funcionario_id: 9,
    })
  })
})
