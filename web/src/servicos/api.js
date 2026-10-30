import axios from 'axios'

/**
 * Cliente HTTP da API. Em desenvolvimento, /api é repassado pelo Vite para a
 * API (ver vite.config.js); em produção, o servidor web faz o mesmo.
 */
export const api = axios.create({ baseURL: '/api', timeout: 30000 })

let obterToken = () => null
const avisos = { naoAutenticado: () => {}, escolherEmpresa: () => {} }

/**
 * Ligações feitas de fora, para evitar import circular: a store de sessão
 * informa o token, e o roteador decide o que fazer quando o login cai ou
 * quando a API pede a escolha da empresa.
 */
export function configurarApi({ token, aoPerderLogin, aoPedirEmpresa }) {
  if (token) obterToken = token
  if (aoPerderLogin) avisos.naoAutenticado = aoPerderLogin
  if (aoPedirEmpresa) avisos.escolherEmpresa = aoPedirEmpresa
}

api.interceptors.request.use((config) => {
  const token = obterToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (resposta) => resposta,
  (erro) => {
    const status = erro.response?.status
    const naoEhLogin = !erro.config?.url?.startsWith('/auth/login')
    if (status === 401 && naoEhLogin) avisos.naoAutenticado()
    if (status === 409 && erro.response?.data?.detail === 'Escolha a empresa') avisos.escolherEmpresa()
    return Promise.reject(erro)
  },
)

/** Mensagem legível para mostrar ao usuário. */
export function mensagemDeErro(erro) {
  const detalhe = erro?.response?.data?.detail
  if (typeof detalhe === 'string') return detalhe
  if (Array.isArray(detalhe)) return 'Dados inválidos. Confira os campos.'
  if (erro?.code === 'ECONNABORTED') return 'O servidor demorou para responder.'
  if (!erro?.response) return 'Sem conexão com o servidor.'
  return 'Algo deu errado. Tente de novo.'
}
