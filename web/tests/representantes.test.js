import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QLayout, QPageContainer, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import RepresentantePagina from '@/paginas/consignacao/RepresentantePagina.vue'
import RepresentantesPagina from '@/paginas/consignacao/RepresentantesPagina.vue'
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
  { tipo_cobranca: 'loja', nome: 'Pagamento na loja', percentual: '20.00', padrao: true },
  { tipo_cobranca: 'cliente', nome: 'Cobrança no cliente', percentual: '15.00', padrao: true },
  { tipo_cobranca: 'representante', nome: 'Representante recebe', percentual: '25.00', padrao: false },
]
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
    vi.spyOn(api, 'get').mockResolvedValue({ data: REP })
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: { ...REP, bloqueado: true, motivo_bloqueio: 'Atrasou' } })
    const { wrapper } = await montar(RepresentantePagina, '/consignacao/representantes/3')
    expect(wrapper.text()).toContain('Representante 262 · Maria Ficticia')
    expect(wrapper.text()).toContain('Acerta toda sexta')
    expect(wrapper.text()).toContain('Centro (Anápolis - GO)')

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
    vi.spyOn(api, 'get').mockResolvedValue({ data: REP })
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
})
