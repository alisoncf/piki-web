import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { contemRota, filtrarMenu, MENU } from '@/menu'
import { destino, rotas } from '@/router'

function sessao({ logado = true, empresa = true, permissoes = [] } = {}) {
  return {
    logado,
    precisaEscolherEmpresa: logado && !empresa,
    pode: (p) => !p || permissoes.includes(p),
  }
}

const rota = (name, meta = {}, fullPath = '/') => ({ name, meta, fullPath })

describe('destino das rotas', () => {
  it('manda para o login quem não entrou, guardando para onde ia', () => {
    expect(destino(rota('usuarios', {}, '/acesso/usuarios'), sessao({ logado: false }))).toEqual({
      name: 'login',
      query: { volta: '/acesso/usuarios' },
    })
  })

  it('quem já entrou não volta para o login', () => {
    expect(destino(rota('login', { publica: true }), sessao())).toEqual({ name: 'inicio' })
  })

  it('pede a empresa quando ainda não foi escolhida', () => {
    expect(destino(rota('inicio'), sessao({ empresa: false }))).toEqual({ name: 'escolher-empresa' })
    expect(destino(rota('escolher-empresa'), sessao({ empresa: false }))).toBe(true)
  })

  it('bloqueia tela sem permissão na empresa ativa', () => {
    const tela = rota('usuarios', { permissao: 'acesso.usuarios' })
    expect(destino(tela, sessao())).toEqual({ name: 'inicio' })
    expect(destino(tela, sessao({ permissoes: ['acesso.usuarios'] }))).toBe(true)
  })

  it('deixa trocar de empresa mesmo já tendo uma', () => {
    expect(destino(rota('escolher-empresa'), sessao())).toBe(true)
  })
})

describe('menu por permissão', () => {
  it('esconde itens sem permissão e grupos vazios', () => {
    const titulos = filtrarMenu(MENU, (p) => !p).map((i) => i.titulo)
    expect(titulos).toEqual(['Início'])
  })

  it('mostra o grupo quando há algum item liberado', () => {
    const menu = filtrarMenu(MENU, (p) => !p || p === 'acesso.usuarios')
    const acesso = menu.find((i) => i.titulo === 'Acesso')
    expect(acesso.filhos.map((f) => f.titulo)).toEqual(['Usuários'])
  })

  it('filtra os subgrupos: Cadastros > Clientes some sem clientes.ver', () => {
    const menu = filtrarMenu(MENU, (p) => !p || p === 'funcionarios.ver')
    const cadastros = menu.find((i) => i.titulo === 'Cadastros')
    expect(cadastros.filhos.map((f) => f.titulo)).toEqual(['Funcionários'])
    expect(cadastros.filhos[0].filhos.map((f) => f.titulo)).toEqual(['Funcionários', 'Cargos'])
  })

  it('sabe de qual item e grupo é a página atual', () => {
    const cadastros = MENU.find((i) => i.titulo === 'Cadastros')
    const [clientes, funcionarios] = cadastros.filhos
    expect(contemRota(cadastros, '/cadastros/clientes/7')).toBe(true)
    expect(contemRota(clientes, '/cadastros/setores')).toBe(true)
    expect(contemRota(funcionarios, '/cadastros/setores')).toBe(false)
    expect(contemRota(clientes.filhos[0], '/cadastros/clientes/novo')).toBe(true)
    expect(contemRota(clientes.filhos[0], '/cadastros/clientes-antigos')).toBe(false)
    expect(contemRota(MENU[0], '/cadastros/clientes')).toBe(false)
    expect(contemRota(MENU[0], '/')).toBe(true)
  })
})

describe('rotas de cadastro', () => {
  it('a ficha do funcionário aceita só id numérico', () => {
    const router = createRouter({ history: createMemoryHistory(), routes: rotas })
    expect(router.resolve('/cadastros/funcionarios/7').name).toBe('funcionario')
    expect(router.resolve('/cadastros/funcionarios/novo').name).toBe('funcionario-novo')
    expect(router.resolve('/cadastros/funcionarios/abc').name).toBe('nao-encontrada')
  })
})
