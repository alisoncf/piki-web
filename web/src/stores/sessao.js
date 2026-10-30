import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api, configurarApi } from '@/servicos/api'

const CHAVE = 'piki.token'

function lerToken() {
  try {
    return localStorage.getItem(CHAVE)
  } catch {
    return null
  }
}

function gravarToken(token) {
  try {
    if (token) localStorage.setItem(CHAVE, token)
    else localStorage.removeItem(CHAVE)
  } catch {
    /* navegador sem armazenamento: a sessão dura até fechar a aba */
  }
}

/**
 * Sessão do usuário: quem está logado, em qual empresa e o que pode fazer.
 * Regras no back-end: decisão D10 em docs/decisoes.md.
 */
export const useSessaoStore = defineStore('sessao', () => {
  const token = ref(null)
  const usuario = ref(null)
  const empresa = ref(null)
  const empresas = ref([])
  const permissoes = ref([])
  const ultimaEmpresaId = ref(null)
  const restaurada = ref(false)

  const logado = computed(() => !!token.value && !!usuario.value)
  const precisaEscolherEmpresa = computed(() => logado.value && !empresa.value)
  const podeTrocarEmpresa = computed(() => empresas.value.length > 1)
  /** primeira letra do primeiro e do último nome, para o avatar */
  const iniciais = computed(() => {
    const partes = (usuario.value?.nome || '').trim().split(/\s+/).filter(Boolean)
    if (!partes.length) return '?'
    return (partes[0][0] + (partes.length > 1 ? partes.at(-1)[0] : '')).toUpperCase()
  })

  function pode(permissao) {
    return !permissao || permissoes.value.includes(permissao)
  }

  function aplicarSessao(dados) {
    token.value = dados.access_token
    usuario.value = dados.usuario
    empresa.value = dados.empresa
    empresas.value = dados.empresas
    ultimaEmpresaId.value = dados.ultima_empresa_id ?? ultimaEmpresaId.value
    gravarToken(token.value)
  }

  async function carregarEu() {
    const { data } = await api.get('/auth/eu')
    usuario.value = data.usuario
    empresa.value = data.empresa
    empresas.value = data.empresas
    permissoes.value = data.permissoes
  }

  async function entrar(login, senha) {
    const { data } = await api.post('/auth/login', { login, senha })
    aplicarSessao(data)
    permissoes.value = []
    if (data.empresa) await carregarEu()
    return data
  }

  async function escolherEmpresa(empresaId) {
    const { data } = await api.post('/auth/empresa', { empresa_id: empresaId })
    aplicarSessao(data)
    await carregarEu()
  }

  function sair() {
    token.value = null
    usuario.value = null
    empresa.value = null
    empresas.value = []
    permissoes.value = []
    gravarToken(null)
  }

  /** Recupera a sessão guardada no navegador (uma vez, ao abrir o sistema). */
  async function restaurar() {
    if (restaurada.value) return
    restaurada.value = true
    const guardado = lerToken()
    if (!guardado) return
    token.value = guardado
    try {
      await carregarEu()
    } catch {
      sair()
    }
  }

  configurarApi({ token: () => token.value })

  return {
    token, usuario, empresa, empresas, permissoes, ultimaEmpresaId,
    logado, precisaEscolherEmpresa, podeTrocarEmpresa, iniciais,
    pode, entrar, escolherEmpresa, carregarEu, sair, restaurar,
  }
})
