import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import AcertoPagina from '@/paginas/consignacao/AcertoPagina.vue'
import ComprovanteAcertoPagina from '@/paginas/consignacao/ComprovanteAcertoPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: null }
const MARIA = { id: 5, nome: 'Maria Ficticia', cpf_cnpj: '52998224725' }
const REP = { id: 3, codigo: 262, cliente: MARIA, bloqueado: false, lembrete: null, lembrete_acerto: 'Cobrar a sacola' }
const COM_ELE = [
  { id: 21, transferencia: { id: 1, numero: 4, confirmada_em: '2026-10-01T10:00:00' }, produto: { id: 7, codigo: 12, unidade: 'UN', fracionado: false },
    descricao: 'Perfume Ficticio', preco: '120.00', quantidade: '2.000', restante: '2.000' },
]
const ITEM = { id: 1, ordem: 1, item_transferencia: COM_ELE[0], quantidade: '2.000', preco: '120.00', total: '240.00' }
const ABERTO = {
  id: 4, numero: 9, situacao: 'aberta', representante: REP, para: 'cliente', cliente: { id: 8, nome: 'Freguesa Ficticia', cpf_cnpj: null },
  queima: false, pagamento: 'prazo', tipo_comissao: 'cliente', nome_comissao: 'Cobrança no cliente', percentual: '15.00',
  total_inicial: '240.00', diferenca: '20.00', negociado: '260.00', comissao: '56.00', valor: '260.00', entrada: '0.00', a_prazo: '0.00',
  parcelas: 2, primeiro_vencimento: '2026-12-05', atendida_por: { id: 1, nome: 'Ana' }, autorizada_por: null,
  criado_em: '2026-11-05T10:00:00', confirmada_em: null, itens: [ITEM], pagamentos: [], carne: [], conta_id: null,
}
const FORMAS = [
  { id: 1, nome: 'Dinheiro', tipo: 'dinheiro', parcelas: 1, parcelas_sem_autorizacao: 1 },
  { id: 2, nome: 'Crediário', tipo: 'crediario', parcelas: 10, parcelas_sem_autorizacao: 6 },
]

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/consignacao/transferencias', name: 'transferencias', component: vazio },
      { path: '/consignacao/acertos/novo', name: 'acerto-novo', component: componente === AcertoPagina ? componente : vazio },
      { path: '/consignacao/acertos/:id', name: 'acerto', component: componente === AcertoPagina ? componente : vazio },
      { path: '/consignacao/acertos/:id/comprovante', name: 'comprovante-acerto', component: componente === ComprovanteAcertoPagina ? componente : vazio },
      { path: '/consignacao/acertos/:id/carne', name: 'carne-acerto', component: vazio },
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
  // este computador está no caixa do consignado, aberto
  localStorage.setItem('piki.caixa', JSON.stringify({ empresa_id: 1, id: 2, nome: 'Consignado' }))
}

// o real formatado vem com espaço não separável
const texto = (wrapper) => wrapper.text().replace(/\s/g, ' ')

function botao(wrapper, texto) {
  return wrapper.findAll('button, a').find((b) => b.text().includes(texto))
}

function respostas(acerto) {
  return async (url) => ({
    data: {
      [`/consignacao/acertos/${acerto.id}`]: acerto,
      '/representantes/3/com-ele': COM_ELE,
      '/formas-pagamento': FORMAS,
      '/caixas': [{ id: 2, nome: 'Consignado', sessao: { id: 8 } }],
    }[url],
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
  document.body.innerHTML = ''
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('acerto do consignado', () => {
  it('para o cliente, a prazo: mostra o lembrete, inclui a peça e, passando do limite, pede a gerência', async () => {
    entrar(['consignacao.acertar'])
    window.print = vi.fn()
    vi.spyOn(api, 'get').mockImplementation(respostas(ABERTO))
    let confirmacoes = 0
    const post = vi.spyOn(api, 'post').mockImplementation(async (url) => {
      if (url.endsWith('/confirmar')) {
        confirmacoes += 1
        if (confirmacoes === 1) {
          const erro = new Error('limite')
          erro.response = { status: 403, headers: { 'x-pede-autorizacao': 'sim' }, data: { detail: 'O carnê de R$ 260,00 passa do limite disponível' } }
          throw erro
        }
        return { data: { ...ABERTO, situacao: 'confirmada' } }
      }
      return { data: ABERTO }
    })
    const { wrapper, router } = await montar(AcertoPagina, '/consignacao/acertos/4')
    expect(texto(wrapper)).toContain('Cobrar a sacola')
    expect(texto(wrapper)).toContain('Comissão (15% · Cobrança no cliente)')
    expect(texto(wrapper)).toContain('2x de R$ 130,00 no nome de Freguesa Ficticia')
    expect(texto(wrapper)).toContain('No caixa Consignado')

    await wrapper.find('tbody tr').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/consignacao/acertos/4/itens', { item_transferencia_id: 21, quantidade: '1' })

    await botao(wrapper, 'Confirmar o acerto').trigger('click')
    await flushPromises()
    ;[...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Confirmar')).click()
    await flushPromises()
    expect(document.body.textContent).toContain('passa do limite disponível')
    const campos = [...document.querySelectorAll('.q-dialog input')]
    campos[0].value = 'gerente'
    campos[0].dispatchEvent(new Event('input'))
    campos[1].value = 'senha-gerente'
    campos[1].dispatchEvent(new Event('input'))
    await flushPromises()
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenLastCalledWith('/consignacao/acertos/4/confirmar', {
      sessao_caixa_id: 8, pagamentos: [], autorizacao: { login: 'gerente', senha: 'senha-gerente' } })
    expect(router.currentRoute.value.name).toBe('comprovante-acerto')
  })

  it('para o representante, à vista: o pagamento já vem com o valor, e ele vê o desconto', async () => {
    entrar(['consignacao.acertar'])
    window.print = vi.fn()
    const vista = { ...ABERTO, para: 'representante', cliente: MARIA, pagamento: 'vista', tipo_comissao: 'vista_dinheiro',
      nome_comissao: 'Acerto à vista: dinheiro ou PIX', percentual: '25.00', diferenca: '0.00', negociado: '240.00', comissao: '60.00', valor: '180.00' }
    vi.spyOn(api, 'get').mockImplementation(respostas(vista))
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...vista, situacao: 'confirmada' } })
    const { wrapper } = await montar(AcertoPagina, '/consignacao/acertos/4')
    expect(texto(wrapper)).toContain('Desconto (25% · Acerto à vista: dinheiro ou PIX)')
    expect(texto(wrapper)).toContain('R$ 180,00')
    await botao(wrapper, 'Confirmar o acerto').trigger('click')
    await flushPromises()
    ;[...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Confirmar')).click()
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/consignacao/acertos/4/confirmar', {
      sessao_caixa_id: 8, pagamentos: [{ forma_pagamento_id: 1, valor: '180.00', parcelas: 1 }], autorizacao: null })
  })

  it('o comprovante mostra a comissão e as duplicatas geradas', async () => {
    entrar(['consignacao.acertar'])
    window.print = vi.fn()
    const confirmado = { ...ABERTO, situacao: 'confirmada', confirmada_em: '2026-11-05T11:00:00', conta_id: 30,
      pagamentos: [{ forma_pagamento: { id: 1, nome: 'Dinheiro', tipo: 'dinheiro' }, valor: '20.00', parcelas: 1 }],
      carne: [{ id: 1, numero: 1, vencimento: '2026-12-05', valor: '120.00', comissao: '28.00' }, { id: 2, numero: 2, vencimento: '2027-01-05', valor: '120.00', comissao: '28.00' }] }
    vi.spyOn(api, 'get').mockResolvedValue({ data: confirmado })
    const { wrapper } = await montar(ComprovanteAcertoPagina, '/consignacao/acertos/4/comprovante?imprimir=1')
    expect(api.get).toHaveBeenCalledWith('/consignacao/acertos/4')
    const pagina = texto(wrapper)
    expect(pagina).toContain('Acerto de consignado nº 9')
    expect(pagina).toContain('Freguesa Ficticia')
    expect(pagina).toContain('Comissão (15%)')
    expect(pagina).toContain('Entrada · Dinheiro')
    expect(pagina).toContain('2/2 · 05/01/2027')
    expect(botao(wrapper, 'Carnê')).toBeTruthy()
    expect(window.print).toHaveBeenCalled()
  })
})
