import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { nomeSetor, soDigitos } from '@/servicos/formatos'

/**
 * Busca do endereço pelo CEP numa ficha (cliente, funcionário). Preenche a rua e
 * escolhe o setor que a API achou igual ao bairro. A rua já digitada só é
 * trocada se a pessoa confirmar; sem setor igual, ela escolhe entre os parecidos
 * ou cadastra o bairro como setor novo (se puder editar setores).
 *
 * `campos` diz onde ficam o CEP, a rua e o setor no `form`; `setores` é a lista
 * da tela, onde entram os setores que vierem da busca.
 */
export function usarCep(form, campos, { setores, podeCriarSetor, limiteRua = 60 }) {
  const $q = useQuasar()
  const buscando = ref(false)
  // cidade do último CEP buscado: enquanto o CEP for o mesmo, a lista de setores mostra só os dela
  const cidade = ref(null)
  let cepBuscado = null

  watch(() => form.value[campos.cep], (cep) => {
    if (cep !== cepBuscado) cidade.value = null
  })

  const opcoesSetor = computed(() => cidade.value
    ? setores.value.filter((s) => s.cidade?.id === cidade.value.id || s.id === form.value[campos.setor])
    : setores.value)

  function perguntar(opcoes) {
    return new Promise((resolve) => {
      $q.dialog({ persistent: true, cancel: { flat: true, label: 'Não' }, ok: { label: 'Sim' }, ...opcoes })
        .onOk((valor) => resolve(valor ?? true))
        .onCancel(() => resolve(null))
    })
  }

  function usarSetor(setor) {
    if (!setores.value.some((s) => s.id === setor.id)) setores.value = [...setores.value, setor]
    form.value[campos.setor] = setor.id
  }

  async function trocarRua(logradouro) {
    const nova = logradouro?.slice(0, limiteRua)
    const atual = form.value[campos.rua]?.trim()
    if (!nova || atual === nova) return
    if (atual && !(await perguntar({ title: 'Endereço do CEP', message: `Trocar "${atual}" por "${nova}"?` }))) return
    form.value[campos.rua] = nova
  }

  async function escolherSetor(dados) {
    const atual = setores.value.find((s) => s.id === form.value[campos.setor])
    if (dados.setor) {
      if (atual && atual.id !== dados.setor.id) {
        const trocar = await perguntar({
          title: 'Setor do CEP', message: `Trocar o setor ${nomeSetor(atual)} por ${nomeSetor(dados.setor)}?`,
        })
        if (!trocar) return
      }
      usarSetor(dados.setor)
      return
    }
    if (!dados.cidade) {
      $q.notify({ type: 'warning', message: 'A cidade do CEP não está na lista do IBGE; escolha o setor' })
      return
    }
    const nomeCidade = `${dados.cidade.nome} - ${dados.cidade.uf}`
    if (!dados.bairro) {
      $q.notify({ type: 'info', message: `CEP geral de ${nomeCidade}: escolha o setor na lista` })
      return
    }
    const itens = dados.sugestoes.map((s) => ({ label: nomeSetor(s), value: s.id }))
    if (podeCriarSetor.value) itens.push({ label: `Cadastrar o setor ${dados.bairro} em ${nomeCidade}`, value: 'novo' })
    if (!itens.length) {
      $q.notify({ type: 'warning', message: `O bairro ${dados.bairro} não está cadastrado como setor de ${nomeCidade}` })
      return
    }
    const escolha = await perguntar({
      title: 'Setor do CEP',
      message: `Nenhum setor de ${nomeCidade} tem o nome do bairro ${dados.bairro}.`
        + (dados.sugestoes.length ? ' É algum destes?' : ''),
      options: { type: 'radio', model: itens[0].value, items: itens },
      ok: { label: 'Usar' },
      cancel: { flat: true, label: 'Escolher depois' },
    })
    if (escolha === 'novo') {
      try {
        const { data } = await api.post('/setores', {
          nome: dados.bairro.slice(0, 40), tipo: null, cidade_id: dados.cidade.id, ativo: true, cobradores: [],
        })
        usarSetor(data)
        $q.notify({ type: 'positive', message: `Setor ${data.nome} cadastrado`, timeout: 1500 })
      } catch (e) {
        $q.notify({ type: 'negative', message: mensagemDeErro(e) })
      }
    } else if (escolha !== null) {
      usarSetor(dados.sugestoes.find((s) => s.id === escolha))
    }
  }

  async function buscar() {
    const cep = soDigitos(form.value[campos.cep])
    if (cep.length !== 8 || buscando.value) return
    buscando.value = true
    let dados
    try {
      dados = (await api.get(`/cep/${cep}`)).data
    } catch (e) {
      $q.notify({ type: 'warning', message: mensagemDeErro(e) })
      return
    } finally {
      buscando.value = false
    }
    cepBuscado = form.value[campos.cep]
    cidade.value = dados.cidade
    await trocarRua(dados.logradouro)
    await escolherSetor(dados)
  }

  return { buscando, buscar, opcoesSetor }
}
