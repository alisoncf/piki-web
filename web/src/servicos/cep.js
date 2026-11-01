import { useQuasar } from 'quasar'
import { computed, ref, watch } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { nomeSetor, soDigitos } from '@/servicos/formatos'

/**
 * Busca do endereço pelo CEP numa ficha (cliente, funcionário, empresa). Preenche
 * a rua e, conforme a ficha, o setor que a API achou igual ao bairro ou o bairro
 * e a cidade. O que já estava preenchido só é trocado se a pessoa confirmar; sem
 * setor igual, ela escolhe entre os parecidos ou cadastra o bairro como setor
 * novo (se puder editar setores).
 *
 * `campos` diz onde ficam no `form` o CEP e a rua, e o setor (cliente,
 * funcionário) ou o bairro e a cidade (empresa). `setores` é a lista da tela,
 * onde entram os setores que vierem da busca; `cidade` guarda a cidade escolhida
 * ({ id, nome, uf }), que o campo de cidade usa para mostrar o nome.
 */
export function usarCep(form, campos, {
  setores = ref([]), podeCriarSetor = computed(() => false), cidade: cidadeEscolhida = ref(null), limiteRua = 60,
} = {}) {
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

  async function trocarTexto(campo, valor, limite) {
    const novo = valor?.slice(0, limite)
    const atual = form.value[campo]?.trim()
    if (!novo || atual === novo) return
    if (atual && !(await perguntar({ title: 'Endereço do CEP', message: `Trocar "${atual}" por "${novo}"?` }))) return
    form.value[campo] = novo
  }

  async function trocarCidade(nova) {
    const atual = cidadeEscolhida.value
    if (!nova || form.value[campos.cidade] === nova.id) return
    if (form.value[campos.cidade] && atual) {
      const trocar = await perguntar({
        title: 'Cidade do CEP', message: `Trocar ${atual.nome} - ${atual.uf} por ${nova.nome} - ${nova.uf}?`,
      })
      if (!trocar) return
    }
    form.value[campos.cidade] = nova.id
    cidadeEscolhida.value = nova
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
    await trocarTexto(campos.rua, dados.logradouro, limiteRua)
    if (campos.bairro) await trocarTexto(campos.bairro, dados.bairro, 60)
    if (campos.cidade) {
      if (dados.cidade) await trocarCidade(dados.cidade)
      else $q.notify({ type: 'warning', message: 'A cidade do CEP não está na lista do IBGE; escolha a cidade' })
    }
    if (campos.setor) await escolherSetor(dados)
  }

  return { buscando, buscar, opcoesSetor }
}
