import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QCheckbox, QInput, QLayout, QPageContainer, QSelect, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import ReceberCrediarioPagina from '@/paginas/caixa/ReceberCrediarioPagina.vue'
import ContasReceberPagina from '@/paginas/financeiro/ContasReceberPagina.vue'
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
    { id: 31, conta_id: 7, loja: BAIRRO, venda: null, documento: '02-0000777', origem: 'acerto', conta_cobranca: 'Geral', numero: 1, parcelas: 2, vencimento: '2026-10-13', valor: '300.00', aberto: '300.00', dias_atraso: 20, juros: '10.00' },
    { id: 32, conta_id: 7, loja: BAIRRO, venda: null, documento: '02-0000777', origem: 'acerto', conta_cobranca: 'Geral', numero: 2, parcelas: 2, vencimento: '2026-11-13', valor: '300.00', aberto: '300.00', dias_atraso: 0, juros: '0.00' },
  ],
}

async function montar(caminho = '/caixa/crediario') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/caixa/crediario', name: 'receber-crediario', component: ReceberCrediarioPagina },
      { path: '/financeiro/receber', name: 'contas-receber', component: ContasReceberPagina },
      { path: '/caixa', name: 'caixa', component: { render: () => h('div') } },
    ],
  })
  await router.push(caminho)
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  wrapper.router = router
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

    await wrapper.findComponent(QSelect).vm.$emit('update:modelValue', { como: 'cliente', cliente: { id: 8, nome: 'Freguesa Ficticia', cpf_cnpj: null } })
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
      sessao_caixa_id: 11, cliente_id: 8, valor_recebido: '320.00', voltar_para_geral: false,
      itens: [{ parcela_id: 31, valor: '300.00', juros: '10.00' }],
      pagamentos: [{ forma_pagamento_id: 1, valor: '310.00' }],
    })
    expect(wrapper.text()).toContain('Recebimento 40')
    expect(wrapper.findAll('button').some((b) => b.text().includes('Estornar'))).toBe(true)
  })

  it('contas a receber: filtra, soma e manda as selecionadas para o recebimento', async () => {
    useSessaoStore().permissoes = ['receber.ver', 'caixa.operar']
    const linha = (id, numero, cliente) => ({
      id, conta_id: 7, documento: '02-0000777', origem: 'acerto', loja: BAIRRO, cliente, setor: 'Centro', cidade: 'Goiânia/GO',
      historico: 'MIGR. CONS. 000087', emissao: '2026-09-13', numero, parcelas: 2, vencimento: '2026-10-13', vencimento_inicial: '2026-09-13',
      valor: '300.00', aberto: '300.00', dias_atraso: 20, juros: '10.00',
    })
    const ANA = { id: 8, nome: 'Ana Ficticia', cpf_cnpj: null, bloqueado: true, credito_suspenso: false }
    const BIA = { id: 9, nome: 'Bia Ficticia', cpf_cnpj: null, bloqueado: false, credito_suspenso: false }
    const get = vi.spyOn(api, 'get').mockResolvedValue({
      data: { itens: [linha(31, 1, ANA), linha(32, 2, ANA), linha(40, 1, BIA)], total: 3, soma_valor: '900.00', soma_aberto: '900.00', juros_ao_mes: '5.00' },
    })
    const wrapper = await montar('/financeiro/receber')
    expect(wrapper.text()).toMatch(/3 parcelas · valor R\$\s900,00/)
    expect(wrapper.text()).toContain('Bloqueado')
    expect(wrapper.text()).toContain('inicial 13/09/2026')

    const busca = wrapper.findAllComponents(QInput).find((c) => c.props('label') === 'Cliente (nome ou CPF)')
    await busca.vm.$emit('update:modelValue', 'ana')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(get).toHaveBeenLastCalledWith('/receber/parcelas', { params: expect.objectContaining({ busca: 'ana', situacao: 'aberto', limite: 100, deslocamento: 0 }) })

    const caixas = wrapper.findAllComponents(QCheckbox)
    await caixas[1].vm.$emit('update:modelValue', true) // a primeira é a de "todas"
    await caixas[3].vm.$emit('update:modelValue', true)
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('Receber 2 selecionadas')).trigger('click')
    await flushPromises()
    expect(wrapper.router.currentRoute.value.name).toBe('contas-receber') // a Bia é outra cliente: não vai
    await caixas[3].vm.$emit('update:modelValue', false)
    await caixas[2].vm.$emit('update:modelValue', true)
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('Receber 2 selecionadas')).trigger('click')
    await flushPromises()
    expect(wrapper.router.currentRoute.value.query).toEqual({ cliente: '8', nome: 'Ana Ficticia', parcelas: '31,32' })
  })

  it('vindo das contas a receber, as parcelas chegam marcadas e o valor é distribuído', async () => {
    localStorage.setItem('piki.caixa', JSON.stringify({ empresa_id: 1, id: 5, nome: 'Cx Crediário' }))
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: {
        '/formas-pagamento': [DINHEIRO, CREDIARIO],
        '/caixas': [{ id: 5, nome: 'Cx Crediário', ativo: true, sessao: { id: 11 } }],
        '/crediario/clientes/8/parcelas': PARCELAS,
      }[url],
    }))
    const wrapper = await montar('/caixa/crediario?cliente=8&nome=Freguesa&parcelas=32')
    expect(wrapper.findAllComponents(QCheckbox).map((c) => c.props('modelValue'))).toEqual([false, true])
    const valor = wrapper.findAllComponents(QInput).find((c) => c.props('label') === 'Distribuir um valor')
    await valor.vm.$emit('update:modelValue', '400')
    await wrapper.findAll('form').find((f) => f.text().includes('Distribuir')).trigger('submit')
    await flushPromises()
    // a mais antiga toda (300) e 100 da outra; os juros da atrasada somam à parte
    expect(wrapper.findAllComponents(QCheckbox).map((c) => c.props('modelValue'))).toEqual([true, true])
    expect(wrapper.findAll('input[aria-label^="Valor da parcela"]').map((i) => i.element.value)).toEqual(['300.00', '100.00'])
    expect(wrapper.text()).toMatch(/Total\s*R\$\s410,00/)
  })

  it('contas a receber: põe as selecionadas no prejuízo, com o motivo', async () => {
    useSessaoStore().permissoes = ['receber.ver', 'receber.prejuizo']
    const linha = {
      id: 31, conta_id: 7, documento: '02-0000777', origem: 'venda', loja: BAIRRO,
      cliente: { id: 8, nome: 'Ana Ficticia', cpf_cnpj: null, bloqueado: false, credito_suspenso: false }, setor: null, cidade: null,
      historico: '', emissao: '2020-09-13', numero: 1, parcelas: 1, vencimento: '2020-10-13', vencimento_inicial: '2020-10-13',
      valor: '300.00', aberto: '300.00', dias_atraso: 2000, juros: '0.00', prejuizo: false, prejuizo_em: null, prejuizo_por: null, prejuizo_motivo: null,
    }
    vi.spyOn(api, 'get').mockResolvedValue({ data: { itens: [linha], total: 1, soma_valor: '300.00', soma_aberto: '300.00', juros_ao_mes: '5.00' } })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { alteradas: 1 } })
    const wrapper = await montar('/financeiro/receber')
    await wrapper.findAllComponents(QCheckbox)[1].vm.$emit('update:modelValue', true)
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('Pôr no prejuízo')).trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('o cliente continua devendo')
    const motivo = document.querySelector('.q-dialog input')
    motivo.value = 'Cliente faleceu'
    motivo.dispatchEvent(new Event('input'))
    await flushPromises()
    ;[...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Pôr no prejuízo')).click()
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/receber/prejuizo', { parcelas: [31], motivo: 'Cliente faleceu' })
  })

  it('contas a receber: muda as selecionadas de conta de cobrança', async () => {
    useSessaoStore().permissoes = ['receber.ver', 'receber.cobranca']
    const linha = {
      id: 31, conta_id: 7, documento: '02-0000777', origem: 'venda', loja: BAIRRO, conta_cobranca: 'Geral',
      cliente: { id: 8, nome: 'Ana Ficticia', cpf_cnpj: null, bloqueado: false, credito_suspenso: false }, setor: null, cidade: null,
      historico: '', emissao: '2026-09-13', numero: 1, parcelas: 1, vencimento: '2026-10-13', vencimento_inicial: '2026-10-13',
      valor: '300.00', aberto: '300.00', dias_atraso: 20, juros: '10.00', prejuizo: false, prejuizo_em: null, prejuizo_por: null, prejuizo_motivo: null,
    }
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: url === '/receber/contas-cobranca'
        ? [{ id: 1, nome: 'Geral', padrao: true, ativo: true }, { id: 2, nome: 'José Cobrador', padrao: false, ativo: true }]
        : { itens: [linha], total: 1, soma_valor: '300.00', soma_aberto: '300.00', juros_ao_mes: '5.00' },
    }))
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { alteradas: 1 } })
    const wrapper = await montar('/financeiro/receber')
    await wrapper.findAllComponents(QCheckbox)[1].vm.$emit('update:modelValue', true)
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('Mudar cobrança')).trigger('click')
    await flushPromises()
    ;[...document.querySelectorAll('.q-dialog .q-radio')].find((r) => r.textContent.includes('José Cobrador')).click()
    await flushPromises()
    ;[...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Mudar')).click()
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/receber/cobranca', { parcelas: [31], conta_cobranca_id: 2 })
  })

  it('contas a receber: prorroga as selecionadas para uma data, com a anotação', async () => {
    useSessaoStore().permissoes = ['receber.ver', 'receber.editar']
    const linha = {
      id: 31, conta_id: 7, documento: '02-0000777', numero_documento: '0000777', origem: 'venda', loja: BAIRRO, conta_cobranca: 'Geral', tipo_cobranca: 'cliente',
      cliente: { id: 8, nome: 'Ana Ficticia', cpf_cnpj: null, bloqueado: false, credito_suspenso: false }, setor: null, cidade: null,
      historico: '', emissao: '2026-09-13', numero: 1, parcelas: 1, vencimento: '2026-10-13', vencimento_inicial: '2026-10-13',
      valor: '300.00', aberto: '300.00', dias_atraso: 20, juros: '10.00', prejuizo: false, prejuizo_em: null, prejuizo_por: null, prejuizo_motivo: null,
    }
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: url === '/receber/contas-cobranca' ? [] : { itens: [linha], total: 1, soma_valor: '300.00', soma_aberto: '300.00', juros_ao_mes: '5.00' },
    }))
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { alteradas: 1 } })
    const wrapper = await montar('/financeiro/receber')
    await wrapper.findAllComponents(QCheckbox)[1].vm.$emit('update:modelValue', true)
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('Prorrogar')).trigger('click')
    await flushPromises()
    const campo = (rotulo) => wrapper.findAllComponents(QInput).find((c) => c.props('label')?.startsWith(rotulo))
    await campo('Novo vencimento').vm.$emit('update:modelValue', '2026-11-30')
    await campo('Anotação do contato').vm.$emit('update:modelValue', 'Paga no dia 30')
    await flushPromises()
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/receber/prorrogar', { parcelas: [31], vencimento: '2026-11-30', dias: null, anotacao: 'Paga no dia 30' })
  })

  it('acha pelo número da parcela do carnê e já marca a parcela', async () => {
    localStorage.setItem('piki.caixa', JSON.stringify({ empresa_id: 1, id: 5, nome: 'Cx Crediário' }))
    const achado = { como: 'parcela', cliente: { id: 8, nome: 'Freguesa Ficticia', cpf_cnpj: null }, conta_id: 7, documento: '02-0000777', parcela_id: 32, parcela: '2/2, vence 13/11/2026, falta R$ 300,00' }
    const get = vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: {
        '/formas-pagamento': [DINHEIRO, CREDIARIO],
        '/caixas': [{ id: 5, nome: 'Cx Crediário', ativo: true, sessao: { id: 11 } }],
        '/crediario/busca': [achado],
        '/crediario/clientes/8/parcelas': PARCELAS,
      }[url],
    }))
    const wrapper = await montar()
    const busca = wrapper.findComponent(QSelect)
    const atualizar = vi.fn((f) => f())
    busca.vm.$emit('filter', '0001234', atualizar, vi.fn())
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/crediario/busca', { params: { termo: '0001234' } })
    await busca.vm.$emit('update:modelValue', achado)
    await flushPromises()
    expect(wrapper.findAllComponents(QCheckbox).map((c) => c.props('modelValue'))).toEqual([false, true])
  })
})
