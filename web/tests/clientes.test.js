import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QLayout, QPageContainer, QSelect, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import SelecaoCidade from '@/componentes/SelecaoCidade.vue'
import ClientePagina from '@/paginas/cadastros/ClientePagina.vue'
import ClientesPagina from '@/paginas/cadastros/ClientesPagina.vue'
import ParentescosPagina from '@/paginas/cadastros/ParentescosPagina.vue'
import SetoresPagina from '@/paginas/cadastros/SetoresPagina.vue'
import { api } from '@/servicos/api'
import { formatarDataHora, formatarDocumento, semAcentos } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', cor: '#2f6fb0' }
const FILIAL = { id: 3, codigo: '03', nome: 'FILIAL', cor: '#1f8a80' }
const OUTRA = { id: 4, codigo: '04', nome: 'OUTRA', cor: '#888888' }
const ANAPOLIS = { id: 5, codigo_ibge: '5201108', nome: 'Anápolis', uf: 'GO' }
const SETOR = { id: 2, nome: 'Jundiaí', cidade: ANAPOLIS }

const MARIA = {
  id: 7, nome: 'Maria Teste', cpf_cnpj: '52998224725', bairro: 'Centro', bloqueado: true,
  credito_suspenso: false, setor: SETOR,
}

const FICHA = {
  ...MARIA, tipo: 'F', rg: null, inscricao_estadual: null, data_nascimento: null, sexo: 'F', pai: null, mae: null,
  email: null, cep: null, logradouro: 'Rua Um', numero: '10', complemento: null, ponto_referencia: null,
  setor_id: 2, grupo_id: null, orgao_id: null, local_trabalho: null, endereco_trabalho: null,
  telefone_trabalho: null, cep_trabalho: null, setor_trabalho_id: null, setor_trabalho: null, grupo: null, orgao: null,
  forma_cobranca: 'trabalho', limite_credito: '550.00', recebe_mensagens: true, especial: false, observacao: null,
  telefones: [{ numero: '62999990000', tipo: '3' }],
  referencias: [{ nome: 'Joana', telefone: null, parentesco_id: 1, parentesco: { id: 1, nome: 'Irmã', ativo: true } }],
  data_cadastro: '2010-01-01', data_alteracao: '2023-03-03', empresa_cadastro: FILIAL, anotacoes: [],
}

async function montar(componente, caminho) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/cadastros/clientes', name: 'clientes', component: componente === ClientesPagina ? componente : vazio },
      { path: '/cadastros/clientes/novo', name: 'cliente-novo', component: componente },
      { path: '/cadastros/clientes/:id', name: 'cliente', component: componente },
      { path: '/cadastros/setores', name: 'setores', component: componente },
      { path: '/cadastros/parentescos', name: 'parentescos', component: componente },
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
  sessao.usuario = { nome: 'Bia' }
  sessao.empresa = MATRIZ
  sessao.empresas = [MATRIZ, FILIAL]
  sessao.permissoes = permissoes
}

/** Respostas da API por endereço. */
function responder(respostas) {
  return vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: respostas[url] ?? [] }))
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

describe('formatos', () => {
  it('formata CPF ou CNPJ, data e hora, e compara sem acentos', () => {
    expect(formatarDocumento('52998224725')).toBe('529.982.247-25')
    expect(formatarDocumento('11222333000181')).toBe('11.222.333/0001-81')
    expect(formatarDataHora('2021-10-27T15:49:46')).toBe('27/10/2021 15:49')
    expect(formatarDataHora('2010-01-01')).toBe('01/01/2010')
    expect(semAcentos('JUNDIAÍ')).toBe('jundiai')
  })
})

describe('lista de clientes', () => {
  it('busca na API uma página por vez e mostra a situação', async () => {
    entrar(['clientes.ver'])
    const get = vi.spyOn(api, 'get').mockResolvedValue({ data: { itens: [MARIA], total: 1 } })
    const { wrapper } = await montar(ClientesPagina, '/cadastros/clientes')
    expect(get).toHaveBeenCalledWith('/clientes', { params: { limite: 20, deslocamento: 0 } })
    expect(wrapper.text()).toContain('Maria Teste')
    expect(wrapper.text()).toContain('529.982.247-25')
    expect(wrapper.text()).toContain('Bloqueado')
    expect(wrapper.text()).not.toContain('Novo cliente')
  })
})

describe('ficha do cliente', () => {
  it('novo: envia os padrões e vai para a ficha criada', async () => {
    entrar(['clientes.ver', 'clientes.editar'])
    responder({ '/setores': [SETOR] })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...FICHA, id: 9 } })
    const { wrapper, router } = await montar(ClientePagina, '/cadastros/clientes/novo')

    expect(wrapper.text()).toContain('Novo cliente')
    expect(wrapper.text()).not.toContain('Anotações')
    await wrapper.find('input[maxlength="60"]').setValue('Maria Teste')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(post).toHaveBeenCalledWith('/clientes', expect.objectContaining({
      nome: 'Maria Teste', tipo: 'F', forma_cobranca: 'domicilio', bloqueado: false, limite_credito: '0.00',
      telefones: [], referencias: [],
    }))
    expect(router.currentRoute.value.params.id).toBe('9')
  })

  it('existente: mostra a origem do cadastro e acrescenta anotações', async () => {
    entrar(['clientes.ver', 'clientes.editar'])
    responder({ '/setores': [SETOR], '/clientes/7': FICHA })
    const nova = { id: 1, texto: 'Paga em dia', data_hora: '2026-10-30T10:00:00', usuario: { id: 1, nome: 'Bia' }, empresa: MATRIZ }
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...FICHA, anotacoes: [nova] } })
    const { wrapper } = await montar(ClientePagina, '/cadastros/clientes/7')

    expect(wrapper.text()).toContain('Cliente desde 01/01/2010, em FILIAL')
    expect(wrapper.text()).toContain('Bloqueado')
    expect(wrapper.find('input[maxlength="60"]').element.value).toBe('Maria Teste')

    await wrapper.findAll('textarea').at(-1).setValue('Paga em dia') // a última é a da nova anotação
    const botao = wrapper.findAll('button').find((b) => b.text() === 'Anotar')
    await botao.trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/clientes/7/anotacoes', { texto: 'Paga em dia' })
    expect(wrapper.text()).toContain('30/10/2026 10:00 · Bia · MATRIZ')
  })

  it('sem permissão de editar, só consulta', async () => {
    entrar(['clientes.ver'])
    responder({ '/clientes/7': FICHA })
    const { wrapper } = await montar(ClientePagina, '/cadastros/clientes/7')
    expect(wrapper.text()).not.toContain('Salvar')
    expect(wrapper.text()).not.toContain('Anotar')
    expect(wrapper.find('fieldset').attributes('disabled')).toBeDefined()
  })
})

describe('setores', () => {
  it('cidade do IBGE e vários cobradores (funcionários), que valem para todas as lojas', async () => {
    entrar(['clientes.ver', 'clientes.editar', 'funcionarios.ver'])
    const sidnei = { id: 1, nome: 'Sidnei' }
    const antigo = { id: 2, nome: 'Antigo' } // saiu da empresa, mas continua no setor
    const edmilson = { id: 3, nome: 'Edmilson' }
    const setor = { ...SETOR, tipo: 'BAIRRO', cidade_id: 5, ativo: true, cobradores: [sidnei, antigo] }
    const outro = { id: 3, nome: 'Vila Nova', tipo: null, cidade: null, cidade_id: null, ativo: true, cobradores: [edmilson] }
    const funcionarios = [{ ...sidnei, ativo: true }, { ...antigo, ativo: false }, { ...edmilson, ativo: true }]
    responder({ '/setores': [setor, outro], '/funcionarios': funcionarios })
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: setor })
    const { wrapper } = await montar(SetoresPagina, '/cadastros/setores')
    expect(wrapper.text()).toContain('Anápolis - GO')
    expect(wrapper.text()).toContain('Sidnei')
    expect(wrapper.text()).toContain('Edmilson')

    await wrapper.find('tbody tr').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('Anápolis - GO') // a cidade aparece no campo sem buscar
    const salvar = [...document.querySelectorAll('button')].find((b) => b.textContent.includes('Salvar'))
    salvar.closest('form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/setores/2', { nome: 'Jundiaí', tipo: 'BAIRRO', cidade_id: 5, ativo: true, cobradores: [1, 2] })
  })

  it('a cidade é buscada na API enquanto digita', async () => {
    const get = vi.spyOn(api, 'get').mockResolvedValue({ data: [ANAPOLIS] })
    const wrapper = mount(SelecaoCidade, { props: { modelValue: null }, global: { plugins: [Quasar] } })
    const select = wrapper.findComponent(QSelect)
    const atualizar = vi.fn((f) => f())
    select.vm.$emit('filter', 'a', atualizar, vi.fn()) // uma letra só não busca
    expect(get).not.toHaveBeenCalled()
    select.vm.$emit('filter', 'anap', atualizar, vi.fn())
    await flushPromises()
    expect(get).toHaveBeenCalledWith('/cidades', { params: { busca: 'anap', limite: 20 } })
    expect(select.props('options')).toEqual([ANAPOLIS])

    select.vm.$emit('update:modelValue', 5)
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([5])
    expect(wrapper.emitted('update:cidade')[0]).toEqual([ANAPOLIS])
  })
})

describe('parentescos', () => {
  it('lista e cadastra', async () => {
    entrar(['clientes.ver', 'clientes.editar'])
    responder({ '/parentescos': [{ id: 1, nome: 'Irmã', ativo: true }] })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: {} })
    const { wrapper } = await montar(ParentescosPagina, '/cadastros/parentescos')
    expect(wrapper.text()).toContain('Irmã')

    await wrapper.findAll('button').find((b) => b.text().includes('Novo parentesco')).trigger('click')
    await flushPromises()
    const campo = document.querySelector('input[maxlength="30"]')
    campo.value = 'Tia'
    campo.dispatchEvent(new Event('input'))
    campo.closest('form').dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/parentescos', { nome: 'Tia', ativo: true })
  })
})
