import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QInput, QLayout, QPageContainer, QSelect, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import CampoCep from '@/componentes/CampoCep.vue'
import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
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

describe('busca do CEP', () => {
  const JAIARA = { id: 4, nome: 'JAIARA', cidade: ANAPOLIS }
  const OUTRA_CIDADE = { id: 8, nome: 'Centro', cidade: { id: 6, codigo_ibge: '5208707', nome: 'Goiânia', uf: 'GO' } }
  const ENDERECO = {
    cep: '75110010', logradouro: 'Rua Amaro Pires', complemento: null, bairro: 'Jundiaí', cidade: ANAPOLIS,
    setor: SETOR, sugestoes: [],
  }

  // valor de um campo de texto da ficha, pelo rótulo
  function valor(wrapper, rotulo) {
    return wrapper.findAllComponents(QInput).find((c) => c.props('label') === rotulo).props('modelValue')
  }

  function botoes(texto) {
    return [...document.querySelectorAll('button')].filter((b) => b.textContent.trim() === texto)
  }

  async function buscarCep(wrapper, indice = 0) {
    const campo = wrapper.findAllComponents(CampoCep).at(indice)
    campo.vm.$emit('update:modelValue', '75110010')
    await flushPromises()
    await campo.find('button[aria-label="Buscar o endereço do CEP"]').trigger('click')
    await flushPromises()
  }

  it('traz a rua e o setor igual ao bairro', async () => {
    entrar(['clientes.ver', 'clientes.editar'])
    const get = responder({ '/setores': [SETOR, JAIARA, OUTRA_CIDADE], '/cep/75110010': ENDERECO })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...FICHA, id: 9 } })
    const { wrapper } = await montar(ClientePagina, '/cadastros/clientes/novo')

    await buscarCep(wrapper)
    expect(get).toHaveBeenCalledWith('/cep/75110010')
    expect(valor(wrapper, 'Logradouro')).toBe('Rua Amaro Pires')
    expect(wrapper.text()).toContain('Jundiaí (Anápolis - GO)')
    // a lista de setores mostra só os da cidade do CEP
    const setor = wrapper.findAllComponents(SelecaoBusca).find((s) => s.props('modelValue') === SETOR.id)
    expect(setor.props('opcoes').map((s) => s.id)).toEqual([SETOR.id, JAIARA.id])

    await wrapper.find('input[maxlength="60"]').setValue('Maria Teste')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/clientes', expect.objectContaining({
      cep: '75110010', logradouro: 'Rua Amaro Pires', setor_id: SETOR.id, setor_trabalho_id: null,
    }))
  })

  it('pergunta antes de trocar a rua; sem setor igual, oferece os parecidos ou cadastrar o bairro', async () => {
    entrar(['clientes.ver', 'clientes.editar'])
    const endereco = { ...ENDERECO, bairro: 'Jardim Jaiara', setor: null, sugestoes: [JAIARA] }
    responder({ '/setores': [SETOR, JAIARA], '/cep/75110010': endereco })
    const novoSetor = { id: 11, nome: 'Jardim Jaiara', cidade: ANAPOLIS }
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: novoSetor })
    const { wrapper } = await montar(ClientePagina, '/cadastros/clientes/novo')
    await wrapper.findAllComponents(QInput).find((c) => c.props('label') === 'Logradouro').find('input').setValue('Rua digitada')

    await buscarCep(wrapper)
    expect(document.body.textContent).toContain('Trocar "Rua digitada" por "Rua Amaro Pires"?')
    botoes('Não').at(-1).click()
    await flushPromises()
    expect(valor(wrapper, 'Logradouro')).toBe('Rua digitada')

    // a pergunta do setor abre quando a da rua termina de fechar
    await vi.waitFor(() => expect(document.body.textContent)
      .toContain('Nenhum setor de Anápolis - GO tem o nome do bairro Jardim Jaiara. É algum destes?'))
    expect(document.body.textContent).toContain('JAIARA (Anápolis - GO)')
    const cadastrar = [...document.querySelectorAll('.q-radio')].find((r) => r.textContent.includes('Cadastrar o setor Jardim Jaiara'))
    cadastrar.click()
    await flushPromises()
    botoes('Usar').at(-1).click()
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/setores', { nome: 'Jardim Jaiara', tipo: null, cidade_id: 5, ativo: true, cobradores: [] })
    expect(wrapper.text()).toContain('Jardim Jaiara (Anápolis - GO)')
  })

  it('o CEP do trabalho preenche o endereço e o setor do trabalho', async () => {
    entrar(['clientes.ver', 'clientes.editar'])
    responder({ '/setores': [SETOR], '/cep/75110010': ENDERECO })
    const { wrapper } = await montar(ClientePagina, '/cadastros/clientes/novo')
    await buscarCep(wrapper, 1)
    const setores = wrapper.findAllComponents(SelecaoBusca).map((s) => s.props('modelValue'))
    expect(setores).toContain(SETOR.id)
    expect(valor(wrapper, 'Logradouro')).toBe('') // a rua de casa não muda
    expect(valor(wrapper, 'Endereço do trabalho')).toBe('Rua Amaro Pires')
  })

  it('CEP não encontrado: avisa e não muda nada', async () => {
    entrar(['clientes.ver', 'clientes.editar'])
    vi.spyOn(api, 'get').mockImplementation(async (url) => {
      if (url.startsWith('/cep/')) throw { response: { status: 404, data: { detail: 'CEP 75110-010 não encontrado' } } }
      return { data: [SETOR] }
    })
    const { wrapper } = await montar(ClientePagina, '/cadastros/clientes/novo')
    const notify = vi.spyOn(wrapper.vm.$q, 'notify')
    await buscarCep(wrapper)
    expect(notify).toHaveBeenCalledWith({ type: 'warning', message: 'CEP 75110-010 não encontrado' })
    expect(valor(wrapper, 'Logradouro')).toBe('')
  })

  it('o botão só busca com o CEP completo', async () => {
    const wrapper = mount(CampoCep, { props: { modelValue: '7511' }, global: { plugins: [Quasar] } })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    await wrapper.setProps({ modelValue: '75110010' })
    await wrapper.find('input').trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('buscar')).toHaveLength(1)
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
