import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import InutilizarNumerosPagina from '@/paginas/notas/InutilizarNumerosPagina.vue'
import NotaVendaPagina from '@/paginas/notas/NotaVendaPagina.vue'
import NotasPagina from '@/paginas/notas/NotasPagina.vue'
import OperacoesNotaPagina from '@/paginas/notas/OperacoesNotaPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: null }
const CHAVE = '52261111222333000181651010000000011234567890'
const NOTA = {
  id: 8, ambiente: '2', modelo: '65', serie: 101, numero: 1, chave: CHAVE, situacao: 'autorizada', venda_id: 3,
  emitida_em: '2026-11-03T10:00:00', emitida_por: { id: 4, nome: 'Davi Caixa' }, valor: '200.00', codigo_retorno: '100',
  motivo_retorno: 'Autorizado o uso da NF-e', protocolo: '152260000000123', autorizada_em: '2026-11-03T10:00:01',
  cancelada_em: null, cancelada_por: null, justificativa_cancelamento: null, protocolo_cancelamento: null,
}
const DANFE = {
  situacao: 'autorizada', emitente: { razao_social: 'LOJA FICTICIA LTDA', cnpj: '11222333000181', inscricao_estadual: '100000001', endereco: 'RUA FICTICIA, 10' },
  itens: [{ codigo: '1', descricao: 'NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL', quantidade: '2.0000', unidade: 'UN', preco: '100.0000', total: '200.00' }],
  produtos: '200.00', descontos: '0.00', outros: '0.00', total: '200.00', pagamentos: [{ tipo: '01', descricao: null, valor: '250.00' }],
  troco: '50.00', consumidor: null, numero: 1, serie: 101, emissao: '2026-11-03T10:00:00-03:00', ambiente: '2', chave: CHAVE,
  url_consulta: 'www.sefaz.go.gov.br/nfce/consulta', protocolo: '152260000000123', autorizada_em: '2026-11-03T10:00:01',
  qrcode: 'https://homolog.sefaz.go.gov.br/x?p=1', qrcode_svg: '<svg class="qr"></svg>', informacoes: 'Venda 15',
}

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/vendas', name: 'vendas', component: vazio },
      { path: '/notas', name: 'notas', component: componente === NotasPagina ? componente : vazio },
      { path: '/vendas/:id/nota', name: 'nota-venda', component: componente === NotaVendaPagina ? componente : vazio },
      { path: '/vendas/:id/carne', name: 'carne', component: vazio },
      { path: '/notas/operacoes', name: 'operacoes-nota', component: componente === OperacoesNotaPagina ? componente : vazio },
      { path: '/notas/inutilizar', name: 'inutilizar-numeros', component: componente === InutilizarNumerosPagina ? componente : vazio },
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
  sessao.usuario = { nome: 'Davi Caixa' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = permissoes
}

function botao(wrapper, texto) {
  return wrapper.findAll('button, a').find((b) => b.text().includes(texto))
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
  window.print = vi.fn()
})

describe('notas fiscais', () => {
  it('logo depois de receber, emite a NFC-e, imprime o DANFE e segue para o carnê', async () => {
    entrar(['caixa.operar'])
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/vendas/3/nota' ? null : DANFE }))
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: NOTA })
    const { wrapper } = await montar(NotaVendaPagina, '/vendas/3/nota?emitir=1&depois=carne')
    expect(post).toHaveBeenCalledWith('/vendas/3/nota')
    expect(api.get).toHaveBeenCalledWith('/notas/8/danfe')
    expect(window.print).toHaveBeenCalled()
    const texto = wrapper.text()
    expect(texto).toContain('Autorizada')
    expect(texto).toContain('EMITIDA EM AMBIENTE DE HOMOLOGAÇÃO - SEM VALOR FISCAL')
    expect(texto).toContain('5226 1111 2223 3300 0181')
    expect(texto).toContain('CONSUMIDOR NÃO IDENTIFICADO')
    expect(texto).toMatch(/Troco R\$\s*50,00/)
    expect(texto).toContain('Protocolo de autorização: 152260000000123')
    expect(wrapper.find('.qrcode svg').exists()).toBe(true)
    expect(botao(wrapper, 'Imprimir o carnê')).toBeDefined()
  })

  it('aberta pela venda, sem nota: não emite sozinha, só no botão', async () => {
    entrar(['caixa.operar'])
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/vendas/3/nota' ? null : DANFE }))
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: NOTA })
    const { wrapper } = await montar(NotaVendaPagina, '/vendas/3/nota')
    expect(post).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('A venda ainda não tem NFC-e')
    await botao(wrapper, 'Emitir a NFC-e').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/vendas/3/nota')
    expect(wrapper.text()).toContain('Autorizada')
  })

  it('a rejeitada mostra o motivo e transmite de novo', async () => {
    entrar(['caixa.operar'])
    const rejeitada = { ...NOTA, situacao: 'rejeitada', codigo_retorno: '778', motivo_retorno: 'Rejeicao: NCM inexistente', protocolo: null }
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/vendas/3/nota' ? rejeitada : DANFE }))
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: NOTA })
    const { wrapper } = await montar(NotaVendaPagina, '/vendas/3/nota')
    expect(post).not.toHaveBeenCalled() // só abre: não emite sozinha
    expect(wrapper.text()).toContain('778 - Rejeicao: NCM inexistente')
    await botao(wrapper, 'Transmitir de novo').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/vendas/3/nota')
    expect(wrapper.text()).toContain('Autorizada')
  })

  it('lista as notas e cancela com justificativa', async () => {
    entrar(['notas.ver', 'notas.cancelar'])
    vi.spyOn(api, 'get').mockResolvedValue({ data: [NOTA] })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...NOTA, situacao: 'cancelada' } })
    const { wrapper } = await montar(NotasPagina, '/notas')
    expect(api.get).toHaveBeenCalledWith('/notas', expect.objectContaining({ params: expect.objectContaining({ inicio: expect.any(String) }) }))
    expect(wrapper.text()).toContain('1 · série 101')
    expect(botao(wrapper, 'Consultar')).toBeUndefined() // sem notas.emitir
    await botao(wrapper, 'Cancelar').trigger('click')
    await flushPromises()
    const campo = document.querySelector('.q-dialog input')
    campo.value = 'Cliente desistiu da compra'
    campo.dispatchEvent(new Event('input'))
    await flushPromises()
    const ok = [...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Cancelar a nota'))
    ok.click()
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/notas/8/cancelar', { justificativa: 'Cliente desistiu da compra' })
    expect(wrapper.text()).toContain('Cancelada')
  })

  it('busca as lacunas da série e inutiliza a faixa escolhida', async () => {
    entrar(['notas.inutilizar'])
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: {
        '/notas/series': [{ modelo: '65', serie: 101, ultimo: 8 }],
        '/notas/inutilizacoes': [],
        '/notas/lacunas': { faixas: [{ inicial: 2, final: 3 }, { inicial: 7, final: 8 }], pendentes: [5] },
      }[url],
    }))
    const feita = { id: 1, ambiente: '2', modelo: '65', serie: 101, inicial: 2, final: 3, justificativa: 'Notas rejeitadas e largadas', protocolo: '152260000000777', homologada_em: '2026-11-03T11:00:00', feita_por: { id: 1, nome: 'Caio' } }
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: feita })
    const { wrapper } = await montar(InutilizarNumerosPagina, '/notas/inutilizar')
    await botao(wrapper, 'Buscar lacunas').trigger('click')
    await flushPromises()
    expect(api.get).toHaveBeenCalledWith('/notas/lacunas', { params: { modelo: '65', serie: 101, desde: expect.any(String) } })
    expect(wrapper.text()).toContain('Consulte-as antes')
    await wrapper.findAll('.q-item').find((i) => i.text().includes('Do 2 ao 3')).trigger('click')
    const justificativa = wrapper.findAllComponents({ name: 'QInput' }).find((c) => c.props('label')?.startsWith('Justificativa'))
    await justificativa.vm.$emit('update:modelValue', 'Notas rejeitadas e largadas')
    await flushPromises()
    await botao(wrapper, 'Inutilizar').trigger('click')
    await flushPromises()
    const ok = [...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Inutilizar'))
    ok.click()
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/notas/inutilizacoes', { modelo: '65', serie: 101, inicial: 2, final: 3, justificativa: 'Notas rejeitadas e largadas' })
    expect(wrapper.text()).toContain('152260000000777')
  })

  it('a NF-e mostra o DANFE em PDF, A4', async () => {
    entrar(['caixa.operar'])
    globalThis.URL.createObjectURL = vi.fn(() => 'blob:danfe')
    globalThis.URL.revokeObjectURL = vi.fn()
    const nfe = { ...NOTA, modelo: '55', destinatario: 'Freguesa Ficticia' }
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/vendas/3/nota' ? nfe : new Blob(['%PDF']) }))
    const { wrapper } = await montar(NotaVendaPagina, '/vendas/3/nota?modelo=55')
    expect(api.get).toHaveBeenCalledWith('/notas/8/danfe.pdf', { responseType: 'blob' })
    expect(wrapper.text()).toContain('NF-e da venda')
    expect(wrapper.text()).toContain('NF-e 1 · série 101 · Freguesa Ficticia')
    expect(wrapper.find('iframe').attributes('src')).toBe('blob:danfe')
  })

  it('edita a natureza e o CFOP da operação', async () => {
    entrar(['notas.configurar'])
    const VENDA = { id: 1, uso: 'venda', natureza: 'Venda de produtos', tipo: '1', finalidade: '1', cfop_estado: '5102', cfop_fora: '6102' }
    vi.spyOn(api, 'get').mockResolvedValue({ data: [VENDA] })
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: { ...VENDA, cfop_fora: '6108' } })
    const { wrapper } = await montar(OperacoesNotaPagina, '/notas/operacoes')
    await wrapper.find('tbody tr').trigger('click')
    await flushPromises()
    const campo = wrapper.findAllComponents({ name: 'QInput' }).find((c) => c.props('label') === 'CFOP para fora *')
    await campo.vm.$emit('update:modelValue', '6108')
    await flushPromises()
    ;[...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Salvar')).click()
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/notas/operacoes/1', { natureza: 'Venda de produtos', tipo: '1', finalidade: '1', cfop_estado: '5102', cfop_fora: '6108' })
    expect(wrapper.text()).toContain('6108')
  })
})
