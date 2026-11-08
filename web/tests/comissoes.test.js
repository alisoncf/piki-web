import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import ComissoesPagina from '@/paginas/consignacao/ComissoesPagina.vue'
import ComprovanteComissaoPagina from '@/paginas/consignacao/ComprovanteComissaoPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: null }
const REP = { id: 3, codigo: 262, cliente: { id: 5, nome: 'Maria Ficticia', cpf_cnpj: null }, bloqueado: false }
const LINHA = { id: 1, acerto: '9', data_acerto: '2026-10-01', cliente: 'Freguesa Ficticia', parcela: '1/3', vencimento: '2026-10-05',
  valor_parcela: '100.00', falta_na_parcela: null, valor: '30.00', pago: '0.00', situacao: 'aberta', liberada: true }
const RELATORIO = { comissao: '80.00', pago: '0.00', liberado: '30.00', a_vencer: '50.00', quantas: 1, linhas: [LINHA] }
const FEITO = { id: 11, data_hora: '2026-11-01T10:00:00', valor: '20.00', forma: 'Dinheiro', usuario: 'Ana', estornado_em: null, estornado_por: null, do_vb6: false }
const FORMAS = [{ id: 1, nome: 'Dinheiro', tipo: 'dinheiro' }, { id: 2, nome: 'Crediário', tipo: 'crediario' }]

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/consignacao/comissoes', name: 'comissoes', component: componente === ComissoesPagina ? componente : vazio },
      { path: '/consignacao/comissoes/pagamentos/:id', name: 'comprovante-comissao', component: componente === ComprovanteComissaoPagina ? componente : vazio },
    ],
  })
  await router.push(caminho)
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}

function entrar(permissoes) {
  const sessao = useSessaoStore()
  sessao.usuario = { nome: 'Ana' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = permissoes
  localStorage.setItem('piki.caixa', JSON.stringify({ empresa_id: 1, id: 2, nome: 'Consignado' }))
}

const texto = (wrapper) => wrapper.text().replace(/\s/g, ' ')

function respostas() {
  return async (url) => ({
    data: {
      '/representantes/3/comissoes': RELATORIO,
      '/representantes/3/comissoes/pagamentos': [FEITO],
      '/formas-pagamento': FORMAS,
      '/caixas': [{ id: 2, nome: 'Consignado', sessao: { id: 8 } }],
    }[url],
  })
}

async function escolherRepresentante(wrapper) {
  const pagina = wrapper.findComponent(ComissoesPagina)
  pagina.vm.$.setupState.representante = REP
  await pagina.vm.$.setupState.carregar()
  await flushPromises()
}

beforeEach(() => {
  setActivePinia(createPinia())
  document.body.innerHTML = ''
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('comissões dos representantes', () => {
  it('mostra o saldo, sugere o liberado e paga saindo do caixa deste computador', async () => {
    entrar(['consignacao.pagar_comissao'])
    window.print = vi.fn()
    vi.spyOn(api, 'get').mockImplementation(respostas())
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { id: 11 } })
    const { wrapper, router } = await montar(ComissoesPagina, '/consignacao/comissoes')
    await escolherRepresentante(wrapper)
    expect(texto(wrapper)).toContain('Saldo liberado')
    expect(texto(wrapper)).toContain('R$ 30,00')
    expect(texto(wrapper)).toContain('Freguesa Ficticia')
    expect(texto(wrapper)).toContain('Sai do Consignado')

    await wrapper.findAll('button').find((b) => b.text().includes('Pagar')).trigger('click')
    await flushPromises()
    ;[...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Confirmar')).click()
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/representantes/3/comissoes/pagamentos', {
      valor: '30.00', forma_pagamento_id: 1, sessao_caixa_id: 8, de: null, ate: null })
    expect(router.currentRoute.value.name).toBe('comprovante-comissao')
  })

  it('quem só consulta não vê o pagamento', async () => {
    entrar(['consignacao.comissoes'])
    vi.spyOn(api, 'get').mockImplementation(respostas())
    const { wrapper } = await montar(ComissoesPagina, '/consignacao/comissoes')
    await escolherRepresentante(wrapper)
    expect(texto(wrapper)).toContain('Saldo liberado')
    expect(texto(wrapper)).not.toContain('Pagar ao representante')
  })

  it('o comprovante mostra o que foi baixado de cada comissão', async () => {
    entrar(['consignacao.comissoes'])
    window.print = vi.fn()
    vi.spyOn(api, 'get').mockResolvedValue({ data: { ...FEITO, representante: REP, linhas: [{ ...LINHA, baixado: '20.00' }] } })
    const { wrapper } = await montar(ComprovanteComissaoPagina, '/consignacao/comissoes/pagamentos/11?imprimir=1')
    const pagina = texto(wrapper)
    expect(pagina).toContain('Comprovante de pagamento de comissão nº 11')
    expect(pagina).toContain('262 · Maria Ficticia')
    expect(pagina).toContain('R$ 20,00 em Dinheiro')
    expect(window.print).toHaveBeenCalled()
  })
})
