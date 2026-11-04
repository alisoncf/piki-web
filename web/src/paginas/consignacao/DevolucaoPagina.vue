<template>
  <!-- a devolução do consignado (D30): escolhe, no que está com o representante, de qual transferência a peça volta -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">{{ devolucao ? `Devolução ${devolucao.numero}` : 'Devolução do representante' }}</div>
      <q-btn flat no-caps icon="list" label="Devoluções" :to="{ name: 'transferencias', query: { aba: 'devolucoes' } }" />
    </div>

    <section v-if="!devolucao" class="cartao q-pa-md">
      <q-select
        v-model="representanteId"
        outlined
        use-input
        autofocus
        input-debounce="300"
        label="Representante (nome, CPF ou código)"
        :options="representantes"
        option-value="id"
        :option-label="(r) => (r?.cliente ? `${r.codigo} · ${r.cliente.nome}` : '')"
        emit-value
        map-options
        @filter="buscarRepresentantes"
        @update:model-value="abrir"
      >
        <template #no-option><q-item><q-item-section class="text-suave">Digite ao menos duas letras ou o código</q-item-section></q-item></template>
      </q-select>
    </section>

    <div v-else class="row q-col-gutter-md">
      <div class="col-12 col-md-7">
        <q-table
          flat
          bordered
          title="Com o representante"
          :rows="comEle"
          :columns="colunasComEle"
          row-key="id"
          :filter="filtro"
          :pagination="{ rowsPerPage: 15 }"
          no-data-label="Nada com o representante nesta loja"
          class="tabela-clicavel"
          @row-click="(_, i) => incluir(i)"
        >
          <template #top-right>
            <q-input v-model="filtro" dense outlined placeholder="Filtrar" clearable>
              <template #prepend><q-icon name="search" /></template>
            </q-input>
          </template>
        </q-table>
        <div class="text-caption text-suave q-mt-xs">Clique no item para devolver uma peça; o mesmo produto aparece uma vez por transferência.</div>
      </div>

      <div class="col-12 col-md-5">
        <section class="cartao q-pa-md q-mb-md">
          <div class="text-weight-medium">{{ devolucao.representante.codigo }} · {{ devolucao.representante.cliente.nome }}</div>
          <q-list v-if="devolucao.itens.length" dense separator class="q-mt-sm">
            <q-item v-for="item in devolucao.itens" :key="item.id">
              <q-item-section>
                <q-item-label>{{ item.item_transferencia.descricao }}</q-item-label>
                <q-item-label caption>Transferência {{ item.item_transferencia.transferencia.numero }} · {{ formatarMoeda(item.item_transferencia.preco) }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-input :model-value="item.quantidade" dense outlined type="number" step="any" min="0" class="campo-quantidade" @change="(v) => alterar(item, v)" />
              </q-item-section>
              <q-item-section side><q-btn flat round dense icon="delete_outline" aria-label="Tirar" @click="alterar(item, 0)" /></q-item-section>
            </q-item>
          </q-list>
          <div v-else class="text-suave q-mt-sm">Nenhum produto ainda.</div>
          <div class="row justify-between text-weight-bold q-mt-sm"><span>Total</span><span>{{ formatarMoeda(devolucao.total) }}</span></div>
          <q-toggle :model-value="devolucao.retificadora" label="Retificadora (corrige um produto transferido errado)" @update:model-value="(v) => salvarDados({ retificadora: v })" />
          <q-input :model-value="devolucao.observacao" outlined dense autogrow label="Observação" maxlength="200" @change="(v) => salvarDados({ observacao: v })" />
        </section>
        <div class="column q-gutter-sm">
          <q-btn unelevated no-caps color="primary" icon="draw" label="Confirmar com a senha do representante" :disable="!devolucao.itens.length" @click="confirmar" />
          <q-btn flat no-caps color="grey-8" icon="delete_outline" label="Descartar" @click="descartar" />
        </div>
      </div>
    </div>

    <dialogo-autorizacao :estado="autorizacao" @responder="responder" />
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DialogoAutorizacao from '@/componentes/DialogoAutorizacao.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { usarAutorizacao } from '@/servicos/autorizacao'
import { formatarCodigoProduto, formatarDataHora, formatarMoeda, formatarQuantidade } from '@/servicos/formatos'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const { autorizacao, responder, comAutorizacao } = usarAutorizacao()
const representantes = ref([])
const representanteId = ref(null)
const devolucao = ref(null)
const comEle = ref([])
const filtro = ref('')

const colunasComEle = [
  { name: 'produto', label: 'Produto', field: (i) => `${formatarCodigoProduto(i.produto.codigo)} · ${i.descricao}`, align: 'left' },
  { name: 'transferencia', label: 'Transferência', field: (i) => `${i.transferencia.numero} · ${formatarDataHora(i.transferencia.confirmada_em).slice(0, 10)}`, align: 'left' },
  { name: 'preco', label: 'Preço', field: 'preco', format: formatarMoeda, align: 'right' },
  { name: 'restante', label: 'Resta', field: 'restante', format: formatarQuantidade, align: 'right' },
]

function buscarRepresentantes(texto, atualizar, cancelar) {
  if (texto.trim().length < 2 && !/^\d+$/.test(texto.trim())) return cancelar()
  api
    .get('/representantes', { params: { busca: texto.trim() } })
    .then(({ data }) => atualizar(() => (representantes.value = data)))
    .catch(() => cancelar())
}

async function carregarComEle() {
  comEle.value = (await api.get(`/representantes/${devolucao.value.representante.id}/com-ele`)).data
}

async function mostrar(dados) {
  devolucao.value = dados
  if (rota.params.id !== String(dados.id)) roteador.replace({ name: 'devolucao', params: { id: dados.id } })
  await carregarComEle()
}

async function acao(fazer) {
  try {
    const { data } = await fazer()
    devolucao.value = data
    return data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e), timeout: 8000 })
    return null
  }
}

async function abrir(id) {
  if (!id) return
  try {
    await mostrar((await api.post('/consignacao/devolucoes', { representante_id: id })).data)
  } catch (e) {
    representanteId.value = null
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

function incluir(item) {
  return acao(() => api.post(`/consignacao/devolucoes/${devolucao.value.id}/itens`, { item_transferencia_id: item.id, quantidade: '1' }))
}

function alterar(item, valor) {
  return acao(() => api.put(`/consignacao/devolucoes/${devolucao.value.id}/itens/${item.id}`, { quantidade: String(Number(valor) || 0) }))
}

function salvarDados(mudanca) {
  const { retificadora, observacao } = { ...devolucao.value, ...mudanca }
  return acao(() => api.put(`/consignacao/devolucoes/${devolucao.value.id}`, { retificadora, observacao: observacao || null }))
}

function confirmar() {
  $q.dialog({
    title: 'Senha do representante',
    message: `${devolucao.value.representante.cliente.nome} confirma que devolve ${devolucao.value.itens.length} produto(s), ${formatarMoeda(devolucao.value.total)}.`,
    prompt: { model: '', type: 'password', isValid: (v) => !!v },
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Confirmar' },
  }).onOk(async (senha) => {
    const url = `/consignacao/devolucoes/${devolucao.value.id}/confirmar`
    // com a devolução do representante bloqueada, pede o login e a senha do gerente e manda de novo
    let data
    try {
      data = await comAutorizacao((liberacao) => api.post(url, { senha, liberacao }))
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e), timeout: 8000 })
      return
    }
    if (!data) return
    $q.notify({ type: 'positive', message: `Devolução ${data.numero} confirmada` })
    roteador.push({ name: 'comprovante-devolucao', params: { id: data.id }, query: { imprimir: 1 } })
  })
}

function descartar() {
  $q.dialog({
    title: 'Descartar a devolução',
    message: 'A devolução ainda não foi confirmada: não mexeu em nada e some.',
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Descartar', color: 'grey-8' },
  }).onOk(async () => {
    try {
      await api.delete(`/consignacao/devolucoes/${devolucao.value.id}`)
      devolucao.value = null
      representanteId.value = null
      roteador.replace({ name: 'devolucao-nova' })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}

onMounted(async () => {
  if (!rota.params.id) return
  try {
    const { data } = await api.get(`/consignacao/devolucoes/${rota.params.id}`)
    if (data.situacao !== 'aberta') return roteador.replace({ name: 'comprovante-devolucao', params: { id: data.id } })
    await mostrar(data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
})
</script>

<style scoped>
.campo-quantidade {
  max-width: 80px;
}
</style>
