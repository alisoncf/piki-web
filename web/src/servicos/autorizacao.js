import { ref } from 'vue'

import { mensagemDeErro } from '@/servicos/api'

/**
 * Pedidos que podem passar do limite (desconto, parcelas, crediário): a API responde 403 com o
 * cabeçalho X-Pede-Autorizacao, a tela pede o login e a senha de quem autoriza (DialogoAutorizacao)
 * e manda de novo com eles.
 */
export function usarAutorizacao() {
  const autorizacao = ref({ aberto: false, mensagem: '', login: '', senha: '' })
  let aoResponder = null

  function pedir(mensagem) {
    autorizacao.value = { aberto: true, mensagem, login: '', senha: '' }
    return new Promise((resolver) => (aoResponder = resolver))
  }

  /** O que o diálogo devolve: { login, senha }, ou null se desistiu. */
  function responder(resposta) {
    autorizacao.value.aberto = false
    aoResponder?.(resposta)
    aoResponder = null
  }

  /**
   * Manda o pedido (uma função que recebe a autorização, ou null); se passar do limite, pede a
   * autorização e manda de novo. Devolve os dados da resposta, ou null se a pessoa desistiu; outros
   * erros sobem.
   */
  async function comAutorizacao(pedido) {
    let dados = null
    for (;;) {
      try {
        return (await pedido(dados)).data
      } catch (e) {
        if (e.response?.status !== 403 || !e.response.headers?.['x-pede-autorizacao']) throw e
        dados = await pedir(mensagemDeErro(e))
        if (!dados) return null
      }
    }
  }

  return { autorizacao, responder, comAutorizacao }
}
