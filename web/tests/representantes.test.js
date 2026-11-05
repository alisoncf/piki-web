import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import ComprovanteConsignadoPagina from '@/paginas/consignacao/ComprovanteConsignadoPagina.vue'
import DevolucaoPagina from '@/paginas/consignacao/DevolucaoPagina.vue'
import RepresentantePagina from '@/paginas/consignacao/RepresentantePagina.vue'
import RepresentantesPagina from '@/paginas/consignacao/RepresentantesPagina.vue'
import TransferenciaPagina from '@/paginas/consignacao/TransferenciaPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: null }
const CLIENTE = {
  id: 5, nome: 'Maria Ficticia', cpf_cnpj: '52998224725', logradouro: 'Rua Ficticia', numero: '10', complemento: null,
  cep: '75000000', email: null, setor: { id: 1, nome: 'Centro', cidade: { id: 1, nome: 'Anápolis', uf: 'GO' } },
  telefones: [{ numero: '62999990000', tipo: '3' }],
}
const COMISSOES = [
  { tipo_cobranca: 'loja', nome: 'Pagamento na loja', percentual: '20.00', padrao: true, percentual_padrao: '20.00' },
  { tipo_cobranca: 'cliente', nome: 'Cobrança no cliente', percentual: '15.00', padrao: true, percentual_padrao: '15.00' },
  { tipo_cobranca: 'representante', nome: 'Representante recebe', percentual: '25.00', padrao: false, percentual_padrao: '20.00' },
]
const POSICAO = { limite: '5000.00', em_uso: '420.00', em_uso_atual: '510.00', disponivel: '4580.00', pecas: '5.000', itens: [
  { produto_id: 1, codigo: 1, descricao: 'Perfume Ficticio', quantidade: '3.000', total_transferencia: '360.00', total_atual: '450.00' },
] }
const REP = {
  id: 3, codigo: 262, cliente: CLIENTE, ativo: true, bloqueado: false, limite: '5000.00', motivo_bloqueio: null, tem_senha: true,
  bloqueia_impressao: false, bloqueia_devolucao: false, lembrete: 'Acerta toda sexta', lembrete_acerto: null, observacao: null,
  ultima_conferencia: null, data_cadastro: '2020-01-10', avalista_nome: null, avalista_cpf: null, avalista_rg: null,
  avalista_endereco: null, avalista_telefones: null, avalista_anotacoes: null, comissoes: COMISSOES,
}

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/consignacao/representantes', name: 'representantes', component: componente === RepresentantesPagina ? componente : vazio },
      { path: '/consignacao/representantes/:id', name: 'representante', component: componente === RepresentantePagina ? componente : vazio },
      { path: '/cadastros/clientes/:id', name: 'cliente', component: vazio },
      { path: '/consignacao/transferencias', name: 'transferencias', component: vazio },
      { path: '/consignacao/transferencias/nova', name: 'transferencia-nova', component: componente === TransferenciaPagina ? componente : vazio },
      { path: '/consignacao/transferencias/:id', name: 'transferencia', component: componente === TransferenciaPagina ? componente : vazio },
      { path: '/consignacao/transferencias/:id/comprovante', name: 'comprovante-transferencia', component: componente === ComprovanteConsignadoPagina ? componente : vazio },
      { path: '/consignacao/devolucoes/nova', name: 'devolucao-nova', component: componente === DevolucaoPagina ? componente : vazio },
      { path: '/consignacao/devolucoes/:id', name: 'devolucao', component: componente === DevolucaoPagina ? componente : vazio },
      { path: '/consignacao/devolucoes/:id/comprovante', name: 'comprovante-devolucao', component: componente === ComprovanteConsignadoPagina ? componente : vazio },
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
}

function botao(wrapper, texto) {
  return wrapper.findAll('button, a').find((b) => b.text().includes(texto))
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

describe('representantes', () => {
  it('lista os ativos e busca', async () => {
    entrar(['representantes.ver'])
    vi.spyOn(api, 'get').mockResolvedValue({ data: [REP] })
    const { wrapper } = await montar(RepresentantesPagina, '/consignacao/representantes')
    expect(api.get).toHaveBeenCalledWith('/representantes', { params: { busca: null, so_ativos: true } })
    expect(wrapper.text()).toContain('Maria Ficticia')
    expect(wrapper.text()).toContain('529.982.247-25')
    expect(wrapper.text()).toContain('Liberado')
    expect(botao(wrapper, 'Novo representante')).toBeUndefined() // sem representantes.editar
  })

  it('salva o limite, o bloqueio e as comissões; o vazio volta para a padrão', async () => {
    entrar(['representantes.editar', 'representantes.limites'])
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url.endsWith('/posicao') ? POSICAO : REP }))
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: { ...REP, bloqueado: true, motivo_bloqueio: 'Atrasou' } })
    const { wrapper } = await montar(RepresentantePagina, '/consignacao/representantes/3')
    expect(wrapper.text()).toContain('Representante 262 · Maria Ficticia')
    expect(wrapper.text()).toContain('Acerta toda sexta')
    expect(wrapper.text()).toContain('Centro (Anápolis - GO)')
    expect(wrapper.text()).toMatch(/Em uso \(preço da transferência\)\s*R\$\s420,00/)
    expect(wrapper.text()).toMatch(/Em uso \(preço atual\)\s*R\$\s510,00/)

    const toggle = wrapper.findAllComponents({ name: 'QToggle' }).find((t) => t.props('label') === 'Bloqueado')
    await toggle.vm.$emit('update:modelValue', true)
    await flushPromises()
    const campo = (rotulo) => wrapper.findAllComponents({ name: 'QInput' }).find((c) => c.props('label') === rotulo)
    await campo('Motivo do bloqueio *').vm.$emit('update:modelValue', 'Atrasou')
    const comissoes = wrapper.findAllComponents({ name: 'QInput' }).filter((c) => c.props('suffix') === '%')
    await comissoes[2].vm.$emit('update:modelValue', '') // representante: volta para a padrão
    await comissoes[1].vm.$emit('update:modelValue', '12')
    await flushPromises()
    await botao(wrapper, 'Salvar limite e comissões').trigger('click')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/representantes/3/limites', {
      limite: '5000.00', bloqueado: true, motivo_bloqueio: 'Atrasou', bloqueia_impressao: false, bloqueia_devolucao: false,
      comissoes: [{ tipo_cobranca: 'cliente', percentual: '12' }],
    })
  })

  it('sem representantes.limites, o limite e as comissões só aparecem', async () => {
    entrar(['representantes.editar'])
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url.endsWith('/posicao') ? POSICAO : REP }))
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: REP })
    const { wrapper } = await montar(RepresentantePagina, '/consignacao/representantes/3')
    expect(botao(wrapper, 'Salvar limite e comissões')).toBeUndefined()
    const senha = wrapper.findAllComponents({ name: 'QInput' }).find((c) => c.props('label')?.startsWith('Nova senha'))
    await senha.vm.$emit('update:modelValue', 'gato12')
    await flushPromises()
    await botao(wrapper, 'Trocar a senha').trigger('click')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/representantes/3/senha', { senha: 'gato12' })
  })

  it('no balcão: escolhe o representante, inclui o produto e confirma com a senha dele', async () => {
    entrar(['consignacao.transferir'])
    window.print = vi.fn()
    const aberta = { id: 9, numero: 4, situacao: 'aberta', representante: { id: 3, codigo: 262, cliente: CLIENTE, bloqueado: false, lembrete: 'Acerta toda sexta' },
      total: '0.00', atendida_por: { id: 1, nome: 'Ana' }, criado_em: '2026-11-04T10:00:00', confirmada_em: null, itens: [], avisos: [] }
    const item = { id: 1, ordem: 1, produto: { id: 7, codigo: 12, unidade: 'UN', fracionado: false }, descricao: 'Perfume Ficticio',
      quantidade: '2.000', preco: '120.00', total: '240.00', restante: '0.000' }
    const comItem = { ...aberta, itens: [item], total: '240.00' }
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: {
        '/representantes': [REP],
        '/representantes/3/posicao': { ...POSICAO, limite: '500.00', disponivel: '80.00' },
        '/produtos': { itens: [{ id: 7, codigo: 12, nome: 'Perfume Ficticio', preco_venda: '120.00', estoque: '3.000' }], total: 1 },
        '/consignacao/transferencias/9': { ...comItem, situacao: 'confirmada' },
      }[url],
    }))
    const post = vi.spyOn(api, 'post').mockImplementation(async (url) => ({
      data: url.endsWith('/itens') ? comItem : url.endsWith('/confirmar') ? { ...comItem, situacao: 'confirmada', avisos: [] } : aberta,
    }))
    const { wrapper, router } = await montar(TransferenciaPagina, '/consignacao/transferencias/nova')
    await wrapper.findComponent({ name: 'QSelect' }).vm.$emit('update:modelValue', 3)
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/consignacao/transferencias', { representante_id: 3 })
    expect(router.currentRoute.value.name).toBe('transferencia')
    expect(wrapper.text()).toContain('Acerta toda sexta')

    const busca = wrapper.findAllComponents({ name: 'QInput' }).find((c) => c.props('label')?.startsWith('Código'))
    await busca.vm.$emit('update:modelValue', '12')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/consignacao/transferencias/9/itens', { produto_id: 7, quantidade: '1' })
    // 80 de limite livre, 240 na transferência: passa
    expect(wrapper.text()).toContain('Passa do limite')

    await botao(wrapper, 'Confirmar com a senha').trigger('click')
    await flushPromises()
    const senha = document.querySelector('.q-dialog input')
    senha.value = 'gato'
    senha.dispatchEvent(new Event('input'))
    await flushPromises()
    ;[...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Confirmar')).click()
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/consignacao/transferencias/9/confirmar', { senha: 'gato' })
    expect(router.currentRoute.value.name).toBe('comprovante-transferencia')
  })

  it('o comprovante tem o produto, o preço e a quantidade, e a linha para assinar', async () => {
    entrar(['consignacao.transferir'])
    window.print = vi.fn()
    const confirmada = { id: 9, numero: 4, situacao: 'confirmada', representante: { id: 3, codigo: 262, cliente: CLIENTE, bloqueado: false, lembrete: null },
      total: '240.00', atendida_por: { id: 1, nome: 'Ana' }, criado_em: '2026-11-04T10:00:00', confirmada_em: '2026-11-04T10:05:00', avisos: [],
      itens: [{ id: 1, ordem: 1, produto: { id: 7, codigo: 12, unidade: 'UN', fracionado: false }, descricao: 'Perfume Ficticio',
        quantidade: '2.000', preco: '120.00', total: '240.00', restante: '2.000' }] }
    vi.spyOn(api, 'get').mockResolvedValue({ data: confirmada })
    const { wrapper } = await montar(ComprovanteConsignadoPagina, '/consignacao/transferencias/9/comprovante?imprimir=1')
    const texto = wrapper.text()
    expect(texto).toContain('Transferência de consignado nº 4')
    expect(texto).toContain('262 · Maria Ficticia')
    expect(texto).toContain('00000012 · Perfume Ficticio')
    expect(texto).toMatch(/R\$\s120,00/)
    expect(texto).toContain('Recebi em consignação')
    expect(window.print).toHaveBeenCalled()
  })

  it('devolução: escolhe a peça no que está com ele; bloqueada, pede a liberação do gerente', async () => {
    entrar(['consignacao.transferir'])
    window.print = vi.fn()
    const comEle = [
      { id: 21, transferencia: { id: 1, numero: 4, confirmada_em: '2026-10-01T10:00:00' }, produto: { id: 7, codigo: 12, unidade: 'UN', fracionado: false },
        descricao: 'Perfume Ficticio', preco: '100.00', quantidade: '2.000', restante: '2.000' },
      { id: 22, transferencia: { id: 2, numero: 5, confirmada_em: '2026-11-01T10:00:00' }, produto: { id: 7, codigo: 12, unidade: 'UN', fracionado: false },
        descricao: 'Perfume Ficticio', preco: '120.00', quantidade: '1.000', restante: '1.000' },
    ]
    const aberta = { id: 3, numero: 1, situacao: 'aberta', retificadora: false, observacao: null,
      representante: { id: 3, codigo: 262, cliente: CLIENTE, bloqueado: false, lembrete: null }, total: '0.00',
      atendida_por: { id: 1, nome: 'Ana' }, autorizada_por: null, criado_em: '2026-11-04T10:00:00', confirmada_em: null, itens: [] }
    const comItem = { ...aberta, total: '120.00', itens: [{ id: 1, ordem: 1, item_transferencia: comEle[1], quantidade: '1.000', total: '120.00' }] }
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: { '/representantes': [REP], '/representantes/3/com-ele': comEle }[url] }))
    let confirmacoes = 0
    const post = vi.spyOn(api, 'post').mockImplementation(async (url) => {
      if (url.endsWith('/confirmar')) {
        confirmacoes += 1
        if (confirmacoes === 1) {
          const erro = new Error('bloqueada')
          erro.response = { status: 403, headers: { 'x-pede-autorizacao': 'sim' }, data: { detail: 'A devolução deste representante está bloqueada' } }
          throw erro
        }
        return { data: { ...comItem, situacao: 'confirmada' } }
      }
      return { data: url.endsWith('/itens') ? comItem : aberta }
    })
    const { wrapper, router } = await montar(DevolucaoPagina, '/consignacao/devolucoes/nova')
    await wrapper.findComponent({ name: 'QSelect' }).vm.$emit('update:modelValue', 3)
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/consignacao/devolucoes', { representante_id: 3 })
    // o mesmo produto, uma linha por transferência
    const linhas = wrapper.findAll('tbody tr')
    expect(linhas).toHaveLength(2)
    expect(linhas[1].text()).toContain('5 · 01/11/2026')
    await linhas[1].trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/consignacao/devolucoes/3/itens', { item_transferencia_id: 22, quantidade: '1' })

    await botao(wrapper, 'Confirmar com a senha').trigger('click')
    await flushPromises()
    const senha = document.querySelector('.q-dialog input')
    senha.value = 'gato'
    senha.dispatchEvent(new Event('input'))
    await flushPromises()
    ;[...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.includes('Confirmar')).click()
    await flushPromises()
    expect(document.body.textContent).toContain('A devolução deste representante está bloqueada')
    const campos = [...document.querySelectorAll('.q-dialog input')]
    campos[0].value = 'gerente'
    campos[0].dispatchEvent(new Event('input'))
    campos[1].value = 'senha-gerente'
    campos[1].dispatchEvent(new Event('input'))
    await flushPromises()
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenLastCalledWith('/consignacao/devolucoes/3/confirmar', { senha: 'gato', liberacao: { login: 'gerente', senha: 'senha-gerente' } })
    expect(router.currentRoute.value.name).toBe('comprovante-devolucao')
  })
})

