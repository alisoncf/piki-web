import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QInput, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import FornecedoresPagina from '@/paginas/cadastros/FornecedoresPagina.vue'
import FornecedorPagina from '@/paginas/cadastros/FornecedorPagina.vue'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const BLUMENAU = { id: 8, codigo_ibge: '4202404', nome: 'Blumenau', uf: 'SC' }
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }
const TECIDOS = {
  id: 4, nome: 'Tecidos Fictícios Ltda', nome_fantasia: 'Fictícia Têxtil', cpf_cnpj: '11222333000181', tipo: 'J',
  inscricao_estadual: null, cep: '89010000', logradouro: 'Rua das Flores', numero: '100', complemento: null, bairro: 'Centro',
  cidade_id: 8, cidade: BLUMENAU, email: null, site: null, observacao: null, ativo: true,
  telefones: [{ numero: '4733334444', tipo: '2' }], contatos: [{ nome: 'Rita', funcao: 'Representante', telefone: null, email: null }],
}
const RECEITA = {
  cnpj: '11444777000161', razao_social: 'Toalhas Exemplo Ltda', nome_fantasia: 'Exemplo', situacao: 'ATIVA', cep: '89010000',
  logradouro: 'Rua das Flores', numero: '200', complemento: null, bairro: 'Centro', cidade: BLUMENAU,
  telefones: ['4733335555'], email: 'contato@exemplo.com.br', fornecedor_id: null,
}

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/cadastros/fornecedores', name: 'fornecedores', component: componente === FornecedoresPagina ? componente : vazio },
      { path: '/cadastros/fornecedores/novo', name: 'fornecedor-novo', component: componente },
      { path: '/cadastros/fornecedores/:id', name: 'fornecedor', component: componente },
    ],
  })
  await router.push(caminho)
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}

function entrar(permissoes = ['fornecedores.ver', 'fornecedores.editar']) {
  const sessao = useSessaoStore()
  sessao.usuario = { nome: 'Caio' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ]
  sessao.permissoes = permissoes
}

function campo(wrapper, rotulo) {
  return wrapper.findAllComponents(QInput).find((c) => c.props('label') === rotulo)
}

function botaoDoDialogo(texto) {
  return [...document.querySelectorAll('.q-dialog button')].find((b) => b.textContent.trim() === texto)
}

async function buscarCnpj(wrapper, cnpj) {
  await campo(wrapper, 'CNPJ ou CPF *').vm.$emit('update:modelValue', cnpj)
  await flushPromises()
  await wrapper.find('button[aria-label="Buscar os dados do CNPJ na Receita"]').trigger('click')
  await flushPromises()
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

describe('fornecedores', () => {
  it('lista com fantasia, CNPJ e cidade; a busca ignora acentos', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: [TECIDOS, { ...TECIDOS, id: 5, nome: 'Costureira Exemplo', nome_fantasia: null, cpf_cnpj: '52998224725', cidade: null }] })
    const { wrapper } = await montar(FornecedoresPagina, '/cadastros/fornecedores')
    expect(wrapper.text()).toContain('Fictícia Têxtil')
    expect(wrapper.text()).toContain('11.222.333/0001-81')
    expect(wrapper.text()).toContain('529.982.247-25')
    expect(wrapper.text()).toContain('Blumenau - SC')
    expect(wrapper.text()).toContain('Novo fornecedor')

    await wrapper.findComponent(QInput).vm.$emit('update:modelValue', 'textil')
    await flushPromises()
    expect(wrapper.text()).toContain('Tecidos Fictícios Ltda')
    expect(wrapper.text()).not.toContain('Costureira Exemplo')
  })

  it('novo: a lupa do CNPJ preenche a ficha; salva com contatos', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: RECEITA })
    const post = vi.spyOn(api, 'post').mockImplementation(async (_, corpo) => ({ data: { ...TECIDOS, ...corpo, id: 9, cidade: BLUMENAU } }))
    const { wrapper, router } = await montar(FornecedorPagina, '/cadastros/fornecedores/novo')
    expect(wrapper.text()).toContain('Contatos') // o índice e a seção

    await buscarCnpj(wrapper, '11444777000161')
    expect(api.get).toHaveBeenCalledWith('/cnpj/11444777000161')
    expect(campo(wrapper, 'Razão social *').props('modelValue')).toBe('Toalhas Exemplo Ltda')
    expect(campo(wrapper, 'Número').props('modelValue')).toBe('200')
    expect(wrapper.text()).toContain('Blumenau - SC')

    await wrapper.findAll('button').find((b) => b.text().includes('Adicionar contato')).trigger('click')
    await campo(wrapper, 'Nome *').vm.$emit('update:modelValue', 'Paulo')
    await campo(wrapper, 'Função').vm.$emit('update:modelValue', 'Financeiro')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/fornecedores', expect.objectContaining({
      cpf_cnpj: '11444777000161', nome: 'Toalhas Exemplo Ltda', cidade_id: 8, email: 'contato@exemplo.com.br',
      telefones: [{ numero: '4733335555', tipo: '2' }],
      contatos: [{ nome: 'Paulo', funcao: 'Financeiro', telefone: '', email: '' }],
    }))
    expect(router.currentRoute.value.params.id).toBe('9')
  })

  it('o que já está preenchido só muda se confirmar', async () => {
    entrar()
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/fornecedores/4' ? TECIDOS : { ...RECEITA, cnpj: TECIDOS.cpf_cnpj } }))
    const { wrapper } = await montar(FornecedorPagina, '/cadastros/fornecedores/4')
    await buscarCnpj(wrapper, TECIDOS.cpf_cnpj)
    expect(document.body.textContent).toContain('Trocar o que já está preenchido')
    botaoDoDialogo('Não').click()
    // a resposta do diálogo só chega depois da animação de fechar
    await vi.waitFor(() => expect(campo(wrapper, 'E-mail').props('modelValue')).toBe('contato@exemplo.com.br')) // estava vazio
    expect(campo(wrapper, 'Razão social *').props('modelValue')).toBe('Tecidos Fictícios Ltda') // fica
  })

  it('CNPJ já cadastrado: oferece abrir a ficha dele', async () => {
    entrar()
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: url === '/fornecedores/4' ? TECIDOS : { ...RECEITA, fornecedor_id: 4 } }))
    const { wrapper, router } = await montar(FornecedorPagina, '/cadastros/fornecedores/novo')
    await buscarCnpj(wrapper, '11444777000161')
    expect(document.body.textContent).toContain('já está cadastrado')
    botaoDoDialogo('Sim').click()
    await flushPromises()
    expect(router.currentRoute.value.params.id).toBe('4')
    expect(campo(wrapper, 'Razão social *').props('modelValue')).toBe('Tecidos Fictícios Ltda')
  })

  it('só consulta: sem botão de novo nem de salvar', async () => {
    entrar(['fornecedores.ver'])
    vi.spyOn(api, 'get').mockResolvedValue({ data: TECIDOS })
    const { wrapper } = await montar(FornecedorPagina, '/cadastros/fornecedores/4')
    expect(campo(wrapper, 'Nome *').props('modelValue')).toBe('Rita')
    expect(wrapper.text()).not.toContain('Salvar')
  })
})
