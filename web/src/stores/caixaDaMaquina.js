import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { useSessaoStore } from '@/stores/sessao'

// o caixa em que este computador está: quem entra no caixa aqui deixa o computador nele,
// e a venda é recebida nele sem perguntar
const CHAVE = 'piki.caixa'

function ler() {
  try {
    const valor = JSON.parse(localStorage.getItem(CHAVE))
    return valor && typeof valor === 'object' && valor.id ? valor : null
  } catch {
    return null
  }
}

function gravar(valor) {
  try {
    if (valor) localStorage.setItem(CHAVE, JSON.stringify(valor))
    else localStorage.removeItem(CHAVE)
  } catch {
    // sem armazenamento local: vale só enquanto a página estiver aberta
  }
}

export const useCaixaDaMaquinaStore = defineStore('caixaDaMaquina', () => {
  const guardado = ref(ler())
  const sessao = useSessaoStore()

  /** { id, nome } do caixa deste computador na empresa ativa, ou null. */
  const caixa = computed(() => (guardado.value && guardado.value.empresa_id === sessao.empresa?.id ? guardado.value : null))

  function entrar({ id, nome }) {
    guardado.value = { empresa_id: sessao.empresa?.id, id, nome }
    gravar(guardado.value)
  }

  function sair() {
    guardado.value = null
    gravar(null)
  }

  return { caixa, entrar, sair }
})
