import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { Dialog, Notify, QCheckbox, QInput, QLayout, QPageContainer, QSelect, Quasar } from 'quasar'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import PerfilPagina from '@/paginas/acesso/PerfilPagina.vue'
import UsuarioPagina from '@/paginas/acesso/UsuarioPagina.vue'
import UsuariosPagina from '@/paginas/acesso/UsuariosPagina.vue'
import TrocarSenhaPagina from '@/paginas/TrocarSenhaPagina.vue'
import { destino } from '@/router'
import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

// dados fictícios
const TEMA = { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' }
const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: TEMA }
const FILIAL = { id: 2, codigo: '02', nome: 'FILIAL', tema: TEMA }
const GERENTE = { id: 3, nome: 'Gerente' }
const CAIXA = { id: 4, nome: 'Caixa' }
const JOANA = {
  id: 7, login: 'joana', nome: 'Joana Teste', email: null, ativo: true, administrador: false, trocar_senha: true,
  bloqueado_ate: null, ultimo_login: null, funcionario: { id: 5, nome: 'Joana Teste', apelido: 'JOANA' },
  acessos: [{ empresa: MATRIZ, perfil: CAIXA, ativo: true }],
}

async function montar(componente, caminho, rotas = []) {
  const vazio = { render: () => h('div') }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'inicio', component: vazio },
      { path: '/acesso/usuarios', name: 'usuarios', component: componente === UsuariosPagina ? componente : vazio },
      { path: '/acesso/usuarios/novo', name: 'usuario-novo', component: componente },
      { path: '/acesso/usuarios/:id', name: 'usuario', component: componente },
      { path: '/acesso/perfis', name: 'perfis', component: vazio },
      { path: '/acesso/perfis/novo', name: 'perfil-novo', component: componente },
      { path: '/acesso/perfis/:id', name: 'perfil', component: componente },
      { path: '/senha', name: 'trocar-senha', component: componente },
      { path: '/login', name: 'login', component: vazio },
      ...rotas,
    ],
  })
  await router.push(caminho)
  const casca = { render: () => h(QLayout, () => h(QPageContainer, () => h(RouterView))) }
  const wrapper = mount(casca, { global: { plugins: [[Quasar, { plugins: { Notify, Dialog } }], router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}

function entrar({ administrador = false, permissoes = ['acesso.usuarios', 'acesso.perfis'], trocarSenha = false } = {}) {
  const sessao = useSessaoStore()
  sessao.token = 'x'
  sessao.usuario = { id: 1, nome: 'Ana Gerente', administrador, trocar_senha: trocarSenha }
  sessao.empresa = MATRIZ
  sessao.empresas = administrador ? [MATRIZ, FILIAL] : [MATRIZ]
  sessao.permissoes = permissoes
  return sessao
}

function campo(wrapper, rotulo) {
  return wrapper.findAllComponents(QInput).find((c) => c.props('label') === rotulo)
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

describe('senha provisória', () => {
  const sessao = (trocar) => ({ logado: true, precisaTrocarSenha: trocar, precisaEscolherEmpresa: false, pode: () => true })
  const rota = (name, fullPath = '/') => ({ name, meta: {}, fullPath })

  it('leva para a troca de senha antes de qualquer tela', () => {
    expect(destino(rota('clientes', '/cadastros/clientes'), sessao(true))).toEqual({ name: 'trocar-senha', query: { volta: '/cadastros/clientes' } })
    expect(destino(rota('escolher-empresa'), sessao(true))).toEqual({ name: 'trocar-senha', query: {} })
    expect(destino(rota('trocar-senha'), sessao(true))).toBe(true)
    expect(destino(rota('trocar-senha'), sessao(false))).toBe(true) // pelo menu do usuário
  })

  it('troca a senha e segue para onde ia', async () => {
    const s = entrar({ trocarSenha: true })
    const post = vi.spyOn(api, 'post').mockResolvedValue({})
    vi.spyOn(api, 'get').mockResolvedValue({ data: { usuario: { ...s.usuario, trocar_senha: false }, empresa: MATRIZ, empresas: [MATRIZ], permissoes: [] } })
    const { wrapper, router } = await montar(TrocarSenhaPagina, '/senha?volta=/acesso/usuarios')
    expect(wrapper.text()).toContain('Crie a sua senha')

    await campo(wrapper, 'Senha provisória').vm.$emit('update:modelValue', 'provisoria1')
    await campo(wrapper, 'Senha nova').vm.$emit('update:modelValue', 'Minha-senha')
    await campo(wrapper, 'Repita a senha nova').vm.$emit('update:modelValue', 'Minha-senha')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/auth/senha', { senha_atual: 'provisoria1', senha_nova: 'Minha-senha' })
    expect(s.precisaTrocarSenha).toBe(false)
    expect(router.currentRoute.value.fullPath).toBe('/acesso/usuarios')
  })
})

describe('usuários', () => {
  it('lista com perfil por empresa e avisos de senha e bloqueio', async () => {
    entrar()
    const bloqueado = { ...JOANA, id: 8, nome: 'Beto Bloqueado', trocar_senha: false, bloqueado_ate: '2999-01-01T10:00:00' }
    vi.spyOn(api, 'get').mockResolvedValue({ data: [JOANA, bloqueado, { ...JOANA, id: 9, nome: 'Da Filial', acessos: [{ empresa: FILIAL, perfil: CAIXA, ativo: true }] }] })
    const { wrapper } = await montar(UsuariosPagina, '/acesso/usuarios')
    expect(wrapper.text()).toContain('MATRIZ · Caixa')
    expect(wrapper.text()).toContain('Senha provisória')
    expect(wrapper.text()).toContain('Bloqueado')
    expect(wrapper.text()).not.toContain('Da Filial') // a gerente vê de começo só os da empresa dela
  })

  it('gerente: novo usuário com senha provisória e perfil na empresa dela', async () => {
    entrar()
    vi.spyOn(api, 'get').mockResolvedValue({ data: [GERENTE, CAIXA] })
    const post = vi.spyOn(api, 'post').mockResolvedValue({ data: { ...JOANA, id: 11 } })
    const { wrapper, router } = await montar(UsuarioPagina, '/acesso/usuarios/novo')
    expect(api.get).not.toHaveBeenCalledWith('/funcionarios', expect.anything()) // sem funcionarios.ver

    await campo(wrapper, 'Nome *').vm.$emit('update:modelValue', 'Joana Teste')
    await campo(wrapper, 'Usuário (login) *').vm.$emit('update:modelValue', 'joana')
    await campo(wrapper, 'Senha provisória *').vm.$emit('update:modelValue', 'provisoria1')
    await wrapper.findAllComponents(QSelect).find((s) => s.props('label') === 'Perfil em MATRIZ *').vm.$emit('update:modelValue', CAIXA.id)
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/acesso/usuarios', {
      nome: 'Joana Teste', login: 'joana', email: null, funcionario_id: null, ativo: true, administrador: false,
      senha: 'provisoria1', perfil_id: CAIXA.id,
    })
    expect(router.currentRoute.value.params.id).toBe('11')
    expect(wrapper.text()).not.toContain('Administrador') // só administrador cria administrador
  })

  it('administrador: dá acesso a outra empresa', async () => {
    entrar({ administrador: true, permissoes: ['acesso.usuarios', 'acesso.perfis', 'funcionarios.ver'] })
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({ data: { '/acesso/perfis': [GERENTE, CAIXA], '/acesso/usuarios/7': JOANA }[url] ?? [] }))
    const put = vi.spyOn(api, 'put').mockResolvedValue({ data: { ...JOANA, acessos: [...JOANA.acessos, { empresa: FILIAL, perfil: GERENTE, ativo: true }] } })
    const { wrapper } = await montar(UsuarioPagina, '/acesso/usuarios/7')
    expect(wrapper.text()).toContain('Senha provisória')
    const selecoes = wrapper.findAllComponents(QSelect).filter((s) => s.props('label') === 'Perfil')
    expect(selecoes.map((s) => s.props('modelValue'))).toEqual([CAIXA.id, null])
    await selecoes[1].vm.$emit('update:modelValue', GERENTE.id)
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/acesso/usuarios/7/acessos/2', { perfil_id: GERENTE.id, ativo: true })
  })
})

describe('perfis', () => {
  const CATALOGO = [
    { codigo: 'acesso.usuarios', descricao: 'Gerenciar usuários', area: 'Acesso' },
    { codigo: 'clientes.ver', descricao: 'Consultar clientes', area: 'Clientes' },
    { codigo: 'clientes.editar', descricao: 'Alterar clientes', area: 'Clientes' },
  ]

  it('agrupa por área; quem não é administrador só dá o que tem', async () => {
    const s = entrar({ permissoes: ['acesso.perfis', 'clientes.ver'] })
    vi.spyOn(api, 'get').mockImplementation(async (url) => ({
      data: url === '/acesso/permissoes' ? CATALOGO : { usuarios: [], empresa: MATRIZ, empresas: [MATRIZ], permissoes: s.permissoes, usuario: s.usuario },
    }))
    const post = vi.spyOn(api, 'post').mockImplementation(async (_, corpo) => ({ data: { id: 6, usuarios: 0, ...corpo } }))
    const { wrapper } = await montar(PerfilPagina, '/acesso/perfis/novo')
    expect(wrapper.text()).toContain('Acesso')
    expect(wrapper.text()).toContain('Clientes')
    const caixas = wrapper.findAllComponents(QCheckbox)
    expect(caixas.map((c) => c.props('disable'))).toEqual([true, false, true])

    await campo(wrapper, 'Nome *').vm.$emit('update:modelValue', 'Caixa')
    await wrapper.findAll('button').find((b) => b.text() === 'Marcar todas' && b.element.closest('section').textContent.includes('Clientes')).trigger('click')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(post).toHaveBeenCalledWith('/acesso/perfis', { nome: 'Caixa', descricao: '', desconto_maximo: '0', permissoes: ['clientes.ver'] })
  })
})
