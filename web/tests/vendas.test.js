import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QInput, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import CarnePagina from '@/paginas/vendas/CarnePagina.vue'
import VendaPagina from '@/paginas/vendas/VendaPagina.vue'
import VendasPagina from '@/paginas/vendas/VendasPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }
const DINHEIRO = { id: 1, nome: 'Dinheiro', tipo: 'dinheiro', desconto: '5.00', parcelas: 1, parcelas_sem_autorizacao: 1 }
const CARTAO = { id: 2, nome: 'Cartão de crédito', tipo: 'cartao_credito', desconto: '0.00', parcelas: 10, parcelas_sem_autorizacao: 3 }
const CREDIARIO = { id: 9, nome: 'Crediário', tipo: 'crediario', desconto: '0.00', parcelas: 10, parcelas_sem_autorizacao: 6 }
const DAVI = { id: 4, nome: 'Davi Vendedor' }
const LENCOL = { id: 7, codigo: 12, nome: 'Lençol Ficticio', preco_venda: '100.00', preco_queima: null, estoque: '5.000' }
const ITEM = {
  id: 1, ordem: 1, produto: { id: 7, codigo: 12, unidade: 'UN', fracionado: false }, descricao: 'Lençol Ficticio',
  quantidade: '1.000', preco: '100.00', bruto: '100.00', desconto: '0.00', total: '100.00', disponivel: '0.000', em_queima: false,
}
const VENDA = {
  id: 3, numero: 15, situacao: 'aberta', criado_em: '2026-11-02T10:00:00', vence_em: '2026-11-12T10:00:00', vendedor: DAVI,
  cliente: null, forma_pagamento: null, parcelas: 1, percentual_desconto: '0', subtotal: '0.00', desconto: '0.00', total: '0.00',
  observacao: null, desconto_autorizado_por: null, parcelas_autorizadas_por: null, itens: [], sessao_caixa: null,
  recebida_em: null, recebida_por: null, valor_recebido: null, troco: null, cancelada_em: null, cancelada_por: null,
  motivo_cancelamento: null, avisos: [], comprador: null, consumidor: null, entrega: null, taxa_entrega: '0.00', fechada_em: null,
}
const COM_ITEM = { ...VENDA, itens: [ITEM], subtotal: '100.00', total: '100.00' }

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/vendas', name: 'vendas', component: componente === VendasPagina ? componente : vazio },
      { path: '/vendas/:id', name: 'venda', component: componente === VendaPagina ? componente : vazio },
      { path: '/vendas/:id/carne', name: 'carne', component: componente === CarnePagina ? componente : vazio },
    ],
  })
  await router.push(caminho)
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}

function entrar(permissoes = ['vendas.vender', 'caixa.operar']) {
  const sessao = useSessaoStore()
  sessao.usuario = { nome: 'Davi Vendedor' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = permissoes
}

function botao(wrapper, texto) {
  return wrapper.findAll('button').find((b) => b.text().includes(texto))
}

function gets(venda) {
  return async (url) => ({
    data: {
      '/formas-pagamento': [DINHEIRO, CARTAO],
      '/produtos': { itens: [LENCOL], total: 1 },
      '/caixas': [{ id: 5, nome: 'Cx 02', ativo: true, sessao: { id: 11 } }, { id: 6, nome: 'Cx 03', ativo: true, sessao: null }],
    }[url] ?? venda,
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
  localStorage.clear()
})

describe('vendas', () => {
  it('nova venda abre a tela da venda', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: { itens: [{ ...VENDA, total: '50.00' }], total: 1 } })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: VENDA })
    const { wrapper, router } = await montar(VendasPagina, '/vendas')
    expect(wrapper.text()).toContain('Davi Vendedor')
    await botao(wrapper, 'Nova venda').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/vendas')
    expect(router.currentRoute.value.params.id).toBe('3')
  })

  it('o código lido entra direto na venda e avisa quando falta estoque', async () => {
    entrar()
    vi.spyOn(api, 'get').mockImplementation(gets(VENDA))
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: COM_ITEM })
    const { wrapper } = await montar(VendaPagina, '/vendas/3')
    const busca = wrapper.findAllComponents(QInput).find((c) => c.props('label')?.startsWith('Código'))
    await busca.vm.$emit('update:modelValue', '7891234567895')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(api.get).toHaveBeenCalledWith('/produtos', { params: { busca: '7891234567895', limite: 20 } })
    expect(post).toHaveBeenCalledWith('/vendas/3/itens', { produto_id: 7, quantidade: '1', autorizacao: null })
    expect(wrapper.text()).toContain('Lençol Ficticio')
    expect(wrapper.text()).toContain('Estoque da loja: 0')
  })

  it('desconto acima do limite pede a senha de quem autoriza e manda de novo', async () => {
    entrar()
    vi.spyOn(api, 'get').mockImplementation(gets(COM_ITEM))
    const negado = { response: { status: 403, headers: { 'x-pede-autorizacao': 'sim' }, data: { detail: 'O desconto de 10% passa do seu limite (2%).' } } }
    const autorizada = { ...COM_ITEM, desconto: '10.00', total: '90.00', desconto_autorizado_por: { id: 1, nome: 'Ana Gerente' } }
    const post = vi.spyOn(api, 'post').mockRejectedValueOnce(negado).mockResolvedValueOnce({ data: autorizada })
    const { wrapper } = await montar(VendaPagina, '/vendas/3')

    await botao(wrapper, 'Dar desconto').trigger('click')
    await flushPromises()
    const valor = wrapper.findAllComponents(QInput).find((c) => c.props('label') === 'Desconto em %')
    await valor.vm.$emit('update:modelValue', '10')
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(document.body.textContent).toContain('passa do seu limite (2%)')

    const campos = wrapper.findAllComponents(QInput)
    await campos.find((c) => c.props('label') === 'Login de quem autoriza').vm.$emit('update:modelValue', 'ana')
    await campos.find((c) => c.props('label') === 'Senha').vm.$emit('update:modelValue', 'segredo')
    const formularios = document.querySelectorAll('.q-dialog form')
    formularios[formularios.length - 1].dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenLastCalledWith('/vendas/3/desconto', { percentual: '10', autorizacao: { login: 'ana', senha: 'segredo' } })
    expect(wrapper.text()).toContain('Desconto autorizado por Ana Gerente')
  })

  it('o caixa recebe no caixa aberto e lembra dele', async () => {
    entrar()
    const noDinheiro = { ...COM_ITEM, forma_pagamento: { id: 1, nome: 'Dinheiro', tipo: 'dinheiro' }, situacao: 'fechada', comprador: 'José' }
    vi.spyOn(api, 'get').mockImplementation(gets(noDinheiro))
    const recebida = { ...noDinheiro, situacao: 'recebida', valor_recebido: '120.00', troco: '20.00', recebida_por: DAVI, sessao_caixa: { id: 11, caixa: { id: 5, nome: 'Cx 02' } }, recebida_em: '2026-11-02T11:00:00' }
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: recebida })
    const { wrapper } = await montar(VendaPagina, '/vendas/3')

    await botao(wrapper, 'Receber').trigger('click')
    await flushPromises()
    const valor = wrapper.findAllComponents(QInput).find((c) => c.props('label') === 'Valor recebido')
    await valor.vm.$emit('update:modelValue', '120')
    await flushPromises()
    expect(document.body.textContent).toContain('Troco R$')
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/vendas/3/receber', { sessao_caixa_id: 11, valor_recebido: '120', autorizacao: null })
    expect(localStorage.getItem('piki.caixa')).toBe('5')
    expect(wrapper.text()).toContain('Recebida por Davi Vendedor no Cx 02')
  })

  it('no crediário mostra o limite do cliente e recebe com entrada', async () => {
    entrar()
    const credito = { limite: '500.00', em_aberto: '200.00', disponivel: '300.00', impedimento: null }
    const noCrediario = {
      ...COM_ITEM, forma_pagamento: { id: 9, nome: 'Crediário', tipo: 'crediario' }, parcelas: 2, situacao: 'fechada',
      cliente: { id: 8, nome: 'Freguesa Ficticia', cpf_cnpj: null, bloqueado: false }, credito,
    }
    const getPadrao = gets(noCrediario)
    vi.spyOn(api, 'get').mockImplementation((url, opcoes) =>
      url === '/formas-pagamento' ? Promise.resolve({ data: [DINHEIRO, CARTAO, CREDIARIO] }) : getPadrao(url, opcoes),
    )
    const recebida = {
      ...noCrediario, situacao: 'recebida', credito: null, entrada: '40.00', forma_entrada: { id: 1, nome: 'Dinheiro', tipo: 'dinheiro' },
      valor_recebido: '50.00', troco: '10.00', recebida_por: DAVI, sessao_caixa: { id: 11, caixa: { id: 5, nome: 'Cx 02' } }, recebida_em: '2026-11-02T11:00:00',
      carne: { id: 21, valor: '60.00', parcelas: [{ numero: 1, vencimento: '2026-12-02', valor: '30.00', aberto: '30.00' }, { numero: 2, vencimento: '2027-01-02', valor: '30.00', aberto: '30.00' }] },
    }
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: recebida })
    const { wrapper, router } = await montar(VendaPagina, '/vendas/3')
    expect(wrapper.text()).toContain('Em aberto (todas as lojas)')
    expect(wrapper.text()).toMatch(/Disponível\s*R\$\s300,00/)
    expect(wrapper.text()).not.toContain('Passa do disponível')

    await botao(wrapper, 'Receber').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toMatch(/Carnê: 2x de R\$\s50,00/)
    const campo = (rotulo) => wrapper.findAllComponents(QInput).find((c) => c.props('label')?.startsWith(rotulo))
    await campo('Entrada').vm.$emit('update:modelValue', '40')
    await flushPromises()
    expect(document.body.textContent).toMatch(/Carnê: 2x de R\$\s30,00/)
    await campo('Valor recebido').vm.$emit('update:modelValue', '50')
    await campo('Primeiro vencimento').vm.$emit('update:modelValue', '2026-12-02')
    await flushPromises()
    expect(document.body.textContent).toContain('Troco R$')
    document.querySelector('.q-dialog form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/vendas/3/receber', {
      sessao_caixa_id: 11, valor_recebido: '50', entrada: '40', forma_entrada_id: 1, primeiro_vencimento: '2026-12-02', autorizacao: null,
    })
    expect(router.currentRoute.value.name).toBe('carne')
    expect(router.currentRoute.value.query.imprimir).toBe('1')
  })

  it('o carnê mostra uma parcela por bloco', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({
      data: {
        loja: { nome: 'Loja Ficticia', cnpj: null, endereco: 'Rua A, 1', telefone: null }, venda: 15, data: '2026-11-02T11:00:00',
        cliente: { id: 8, nome: 'Freguesa Ficticia', cpf_cnpj: null, endereco: 'Rua B nº 2', cidade: 'Goiânia/GO' },
        carne: { id: 21, valor: '60.00', parcelas: [{ numero: 1, vencimento: '2026-12-02', valor: '30.00', aberto: '30.00' }, { numero: 2, vencimento: '2027-01-02', valor: '30.00', aberto: '30.00' }] },
      },
    })
    const { wrapper } = await montar(CarnePagina, '/vendas/3/carne')
    expect(api.get).toHaveBeenCalledWith('/vendas/3/carne')
    expect(wrapper.findAll('.parcela')).toHaveLength(2)
    expect(wrapper.text()).toContain('02/01/2027')
    expect(wrapper.text()).toContain('2/2')
  })
  it('venda a consumidor: o vendedor dá o nome e fecha a venda', async () => {
    entrar(['vendas.vender'])
    const noDinheiro = { ...COM_ITEM, forma_pagamento: { id: 1, nome: 'Dinheiro', tipo: 'dinheiro' } }
    vi.spyOn(api, 'get').mockImplementation(gets(noDinheiro))
    const comNome = { ...noDinheiro, comprador: 'José' }
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: comNome })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...comNome, situacao: 'fechada', fechada_em: '2026-11-02T10:30:00' } })
    const { wrapper } = await montar(VendaPagina, '/vendas/3')
    expect(botao(wrapper, 'Receber')).toBeUndefined() // quem recebe é o caixa, e só depois de fechada

    const nome = wrapper.findAllComponents(QInput).find((c) => c.props('label')?.startsWith('Nome de quem está comprando'))
    await nome.vm.$emit('update:modelValue', 'José')
    await nome.vm.$emit('change')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/vendas/3', {
      cliente_id: null, forma_pagamento_id: 1, parcelas: 1, observacao: '', entrega: null, autorizacao: null,
      consumidor: { nome: 'José', cpf: null, dia_nascimento: null, mes_nascimento: null, telefone: null, email: null },
    })
    await botao(wrapper, 'Fechar venda').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/vendas/3/fechar')
    expect(wrapper.text()).toContain('Fechada em 02/11/2026 10:30')
    expect(botao(wrapper, 'Reabrir')).toBeDefined()
  })

  it('o CPF de cliente cadastrado troca o consumidor pelo cliente', async () => {
    entrar(['vendas.vender'])
    const MARIA = { id: 8, nome: 'Maria Ficticia', cpf_cnpj: '52998224725', bloqueado: false }
    const padrao = gets(COM_ITEM)
    vi.spyOn(api, 'get').mockImplementation((url, opcoes) =>
      url === '/consumidores/52998224725' ? Promise.resolve({ data: { cliente: MARIA, consumidor: null } }) : padrao(url, opcoes),
    )
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: { ...COM_ITEM, cliente: MARIA, comprador: MARIA.nome } })
    const { wrapper } = await montar(VendaPagina, '/vendas/3')
    const cpf = wrapper.findAllComponents(QInput).find((c) => c.props('label') === 'CPF')
    await cpf.vm.$emit('update:modelValue', '52998224725')
    await cpf.vm.$emit('change')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/vendas/3', expect.objectContaining({ cliente_id: 8, consumidor: null }))
  })

  it('o produto em queima aparece marcado', async () => {
    entrar()
    vi.spyOn(api, 'get').mockImplementation(gets({ ...COM_ITEM, itens: [{ ...ITEM, em_queima: true }] }))
    const { wrapper } = await montar(VendaPagina, '/vendas/3')
    expect(wrapper.text()).toContain('Lençol Ficticio Queima')
  })
})
