<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Vendas</div>
      <q-btn
        v-if="sessao.pode('vendas.vender')"
        color="primary"
        unelevated
        no-caps
        icon="add_shopping_cart"
        label="Nova venda"
        :loading="criando"
        @click="nova"
      />
    </div>

    <q-table
      v-model:pagination="paginacao"
      flat
      bordered
      :rows="vendas"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :rows-per-page-options="[20, 50, 100]"
      rows-per-page-label="Por página"
      no-data-label="Nenhuma venda"
      loading-label="Carregando..."
      class="tabela-clicavel"
      @request="aoPaginar"
      @row-click="(_, v) => $router.push({ name: v.situacao === 'fechada' && sessao.pode('caixa.operar') ? 'receber-venda' : 'venda', params: { id: v.id } })"
    >
      <template #top>
        <div class="row items-center q-gutter-md full-width">
          <q-input v-model="busca" dense outlined debounce="300" placeholder="Número da venda ou nome de quem comprou" clearable class="col-12 col-sm">
            <template #prepend><q-icon name="search" /></template>
          </q-input>
          <q-btn-toggle v-model="situacao" no-caps unelevated toggle-color="primary" :options="SITUACOES" />
          <q-toggle v-if="sessao.pode('vendas.vender')" v-model="minhas" label="Só as minhas" />
        </div>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="CORES[props.row.situacao]">{{ nomeSituacao(props.row.situacao) }}</q-badge>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarMoeda } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const SITUACOES = [
  { label: 'Abertas', value: 'aberta' },
  { label: 'Fechadas', value: 'fechada' },
  { label: 'Recebidas', value: 'recebida' },
  { label: 'Canceladas', value: 'cancelada' },
  { label: 'Vencidas', value: 'vencida' },
  { label: 'Todas', value: null },
]
const CORES = { aberta: 'warning', fechada: 'primary', recebida: 'positive', cancelada: 'grey', vencida: 'grey-7' }
const nomeSituacao = (s) => SITUACOES.find((x) => x.value === s)?.label.slice(0, -1) ?? s

const $q = useQuasar()
const roteador = useRouter()
const sessao = useSessaoStore()

const vendas = ref([])
const carregando = ref(false)
const criando = ref(false)
const busca = ref('')
// o caixa começa pelas fechadas, que esperam para ser recebidas
const situacao = ref(sessao.pode('caixa.operar') && !sessao.pode('vendas.vender') ? 'fechada' : 'aberta')
const minhas = ref(false)
const paginacao = ref({ page: 1, rowsPerPage: 20, rowsNumber: 0 })

const colunas = [
  { name: 'numero', label: 'Venda', field: 'numero', align: 'left' },
  { name: 'data', label: 'Aberta em', field: 'criado_em', align: 'left', format: formatarDataHora },
  { name: 'vendedor', label: 'Vendedor', field: (v) => v.vendedor.nome, align: 'left' },
  { name: 'comprador', label: 'Comprador', field: (v) => v.comprador ?? v.cliente?.nome ?? '', align: 'left' },
  { name: 'forma', label: 'Pagamento', align: 'left', field: (v) => (v.forma_pagamento ? `${v.forma_pagamento.nome}${v.parcelas > 1 ? ` ${v.parcelas}x` : ''}` : '') },
  { name: 'total', label: 'Total', field: 'total', align: 'right', format: formatarMoeda },
  { name: 'situacao', label: 'Situação', field: 'situacao', align: 'left' },
]

async function carregar() {
  carregando.value = true
  const { page, rowsPerPage } = paginacao.value
  try {
    const params = { limite: rowsPerPage, deslocamento: (page - 1) * rowsPerPage }
    if (busca.value?.trim()) params.busca = busca.value.trim()
    if (situacao.value) params.situacao = situacao.value
    if (minhas.value) params.minhas = true
    const { data } = await api.get('/vendas', { params })
    vendas.value = data.itens
    paginacao.value = { ...paginacao.value, rowsNumber: data.total }
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function aoPaginar({ pagination }) {
  paginacao.value = { ...paginacao.value, page: pagination.page, rowsPerPage: pagination.rowsPerPage }
  carregar()
}

async function nova() {
  criando.value = true
  try {
    const { data } = await api.post('/vendas')
    await roteador.push({ name: 'venda', params: { id: data.id } })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    criando.value = false
  }
}

watch([busca, situacao, minhas], () => {
  paginacao.value = { ...paginacao.value, page: 1 }
  carregar()
})

onMounted(carregar)
</script>
