import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import CampoCep from '@/componentes/CampoCep.vue'
import FuncionarioPagina from '@/paginas/cadastros/FuncionarioPagina.vue'
import FuncionariosPagina from '@/paginas/cadastros/FuncionariosPagina.vue'
import { api } from '@/servicos/api'
import { formatarCpf, formatarTelefone, mascaraTelefone, nomeTipoTelefone } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#f5f5f5', menu: '#222222' } }
const FILIAL = { id: 3, codigo: '03', nome: 'FILIAL', tema: { principal: '#1f8a80', fundo: '#f5f5f5', menu: '#222222' } }
const CARGO = { id: 5, nome: 'Vendedor', vende: true, cobra: false, ativo: true }

const JOANA = {
  id: 7, nome: 'Joana Teste', apelido: 'JOANA', cpf: '52998224725', ativo: true, empresa: MATRIZ, cargo: CARGO,
}
const PEDRO = { id: 8, nome: 'Pedro Teste', apelido: null, cpf: null, ativo: false, empresa: FILIAL, cargo: null }

async function montar(componente, caminho) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/cadastros/funcionarios', name: 'funcionarios', component: componente === FuncionariosPagina ? componente : { render: () => h('div') } },
      { path: '/cadastros/funcionarios/novo', name: 'funcionario-novo', component: componente },
      { path: '/cadastros/funcionarios/:id', name: 'funcionario', component: componente },
    ],
  })
  await router.push(caminho)
  // q-page só aparece dentro de um q-layout
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] } })
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

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
})

describe('formatos', () => {
  it('formata CPF e telefone', () => {
    expect(formatarCpf('52998224725')).toBe('529.982.247-25')
    expect(formatarTelefone('62999990000')).toBe('(62) 99999-0000')
    expect(formatarTelefone('6233334444')).toBe('(62) 3333-4444')
    expect(nomeTipoTelefone('3')).toBe('Celular')
  })

  it('a máscara do telefone cresce para celular', () => {
    expect(mascaraTelefone('6233334444')).toBe('(##) ####-#####')
    expect(mascaraTelefone('62999990000')).toBe('(##) #####-####')
  })
})

describe('lista de funcionários', () => {
  it('mostra os ativos de todas as lojas, com CPF formatado', async () => {
    entrar(['funcionarios.ver'])
    vi.spyOn(api, 'get').mockResolvedValue({ data: [JOANA, PEDRO] })
    const { wrapper } = await montar(FuncionariosPagina, '/cadastros/funcionarios')
    expect(wrapper.text()).toContain('Joana Teste')
    expect(wrapper.text()).toContain('529.982.247-25')
    expect(wrapper.text()).not.toContain('Pedro Teste') // inativo
    // sem permissão de editar, não oferece o botão de novo
    expect(wrapper.text()).not.toContain('Novo funcionário')
  })
})

describe('cadastro de funcionário', () => {
  it('novo: já vem na loja ativa e envia os dados para a API', async () => {
    entrar(['funcionarios.ver', 'funcionarios.editar'])
    vi.spyOn(api, 'get').mockResolvedValue({ data: [CARGO] })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...JOANA, id: 9 } })
    const { wrapper, router } = await montar(FuncionarioPagina, '/cadastros/funcionarios/novo')

    expect(wrapper.text()).toContain('Novo funcionário')
    await wrapper.find('input[maxlength="80"]').setValue('Joana Teste')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(post).toHaveBeenCalledWith('/funcionarios', expect.objectContaining({
      nome: 'Joana Teste', empresa_id: MATRIZ.id, limite_vale: '0.00', telefones: [], setor_id: null,
    }))
    expect(router.currentRoute.value.params.id).toBe('9')
  })

  it('existente: carrega os dados; sem permissão de editar, não mostra o salvar', async () => {
    entrar(['funcionarios.ver'])
    const setor = { id: 2, nome: 'Jundiaí', cidade: { id: 5, codigo_ibge: '5201108', nome: 'Anápolis', uf: 'GO' } }
    const get = vi.spyOn(api, 'get').mockImplementation(async (url) =>
      url === '/cargos'
        ? { data: [CARGO] }
        : { data: { ...JOANA, limite_vale: '10.00', telefones: [{ numero: '62999990000', tipo: '3' }], setor_id: 2, setor } },
    )
    const { wrapper } = await montar(FuncionarioPagina, '/cadastros/funcionarios/7')
    expect(wrapper.find('input[maxlength="80"]').element.value).toBe('Joana Teste')
    // sem a lista de setores (que pede outra permissão), mostra o setor que veio na ficha
    expect(get).not.toHaveBeenCalledWith('/setores')
    expect(wrapper.text()).toContain('Jundiaí (Anápolis - GO)')
    expect(wrapper.text()).not.toContain('Salvar')
    expect(wrapper.find('fieldset').attributes('disabled')).toBeDefined()
  })
})

describe('CEP do funcionário', () => {
  it('traz a rua e o setor; sem editar clientes, não oferece cadastrar o setor', async () => {
    entrar(['funcionarios.ver', 'funcionarios.editar'])
    const anapolis = { id: 5, codigo_ibge: '5201108', nome: 'Anápolis', uf: 'GO' }
    const jaiara = { id: 4, nome: 'JAIARA', cidade: anapolis }
    const respostas = {
      '/cargos': [CARGO],
      '/setores': [jaiara],
      '/cep/75110010': {
        cep: '75110010', logradouro: 'Rua Amaro Pires', complemento: null, bairro: 'Jardim Jaiara', cidade: anapolis,
        setor: null, sugestoes: [jaiara],
      },
    }
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: respostas[url] }))
    const { wrapper } = await montar(FuncionarioPagina, '/cadastros/funcionarios/novo')
    const campo = wrapper.findComponent(CampoCep)
    campo.vm.$emit('update:modelValue', '75110010')
    await flushPromises()
    await campo.find('button').trigger('click')
    await flushPromises()

    expect(wrapper.find('input[maxlength="60"]').element.value).toBe('Rua Amaro Pires')
    expect(document.body.textContent).toContain('JAIARA (Anápolis - GO)')
    expect(document.body.textContent).not.toContain('Cadastrar o setor')
    const usar = [...document.querySelectorAll('button')].filter((b) => b.textContent.trim() === 'Usar').at(-1)
    usar.click()
    await flushPromises()
    expect(wrapper.text()).toContain('JAIARA (Anápolis - GO)')
  })
})
