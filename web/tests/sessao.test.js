import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const EMPRESAS = [
  { id: 1, codigo: '01', nome: 'MATRIZ' },
  { id: 3, codigo: '03', nome: 'FILIAL' },
]

function respostaLogin(empresa) {
  return {
    access_token: `token-${empresa?.id ?? 'sem'}`,
    usuario: { id: 7, login: 'bia', nome: 'Bia Souza', administrador: false },
    empresa,
    empresas: EMPRESAS,
    ultima_empresa_id: 3,
  }
}

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('sessão', () => {
  it('com várias empresas, entra sem empresa ativa e pede a escolha', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({ data: respostaLogin(null) })
    const sessao = useSessaoStore()
    await sessao.entrar('bia', 'x')
    expect(sessao.logado).toBe(true)
    expect(sessao.precisaEscolherEmpresa).toBe(true)
    expect(sessao.podeTrocarEmpresa).toBe(true)
    expect(sessao.ultimaEmpresaId).toBe(3)
    expect(localStorage.getItem('piki.token')).toBe('token-sem')
  })

  it('escolher a empresa troca o token e carrega as permissões', async () => {
    vi.spyOn(api, 'post')
      .mockResolvedValueOnce({ data: respostaLogin(null) })
      .mockResolvedValueOnce({ data: respostaLogin(EMPRESAS[0]) })
    vi.spyOn(api, 'get').mockResolvedValue({
      data: { usuario: respostaLogin().usuario, empresa: EMPRESAS[0], empresas: EMPRESAS, permissoes: ['acesso.usuarios'] },
    })
    const sessao = useSessaoStore()
    await sessao.entrar('bia', 'x')
    await sessao.escolherEmpresa(1)
    expect(api.post).toHaveBeenLastCalledWith('/auth/empresa', { empresa_id: 1 })
    expect(sessao.empresa.nome).toBe('MATRIZ')
    expect(sessao.token).toBe('token-1')
    expect(sessao.pode('acesso.usuarios')).toBe(true)
    expect(sessao.pode('outra.coisa')).toBe(false)
  })

  it('iniciais do usuário para o avatar', () => {
    const sessao = useSessaoStore()
    expect(sessao.iniciais).toBe('?')
    sessao.usuario = { nome: 'bia' }
    expect(sessao.iniciais).toBe('B')
    sessao.usuario = { nome: '  Ana Beatriz  de Souza ' }
    expect(sessao.iniciais).toBe('AS')
  })

  it('sair limpa tudo, inclusive o token guardado', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({ data: respostaLogin(null) })
    const sessao = useSessaoStore()
    await sessao.entrar('bia', 'x')
    sessao.sair()
    expect(sessao.logado).toBe(false)
    expect(localStorage.getItem('piki.token')).toBeNull()
  })

  it('restaura a sessão guardada; se o token não vale mais, sai', async () => {
    localStorage.setItem('piki.token', 'vencido')
    vi.spyOn(api, 'get').mockRejectedValue({ response: { status: 401 } })
    const sessao = useSessaoStore()
    await sessao.restaurar()
    expect(sessao.logado).toBe(false)
    expect(localStorage.getItem('piki.token')).toBeNull()
  })
})
