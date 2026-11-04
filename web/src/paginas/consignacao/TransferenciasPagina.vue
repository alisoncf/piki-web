<template>
  <!-- as transferências e as devoluções do consignado da loja (D30) -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Consignado</div>
      <template v-if="sessao.pode('consignacao.transferir')">
        <q-btn flat no-caps color="primary" icon="move_down" label="Nova devolução" :to="{ name: 'devolucao-nova' }" />
        <q-btn color="primary" unelevated no-caps icon="move_up" label="Nova transferência" class="q-ml-sm" :to="{ name: 'transferencia-nova' }" />
      </template>
    </div>

    <q-tabs v-model="aba" no-caps align="left" active-color="primary" class="q-mb-sm" @update:model-value="trocarAba">
      <q-tab name="transferencias" label="Transferências" />
      <q-tab name="devolucoes" label="Devoluções" />
    </q-tabs>

    <q-table
      flat
      bordered
      :rows="documentos"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 30 }"
      :no-data-label="aba === 'devolucoes' ? 'Nenhuma devolução' : 'Nenhuma transferência'"
      class="tabela-clicavel"
      @row-click="(_, d) => abrir(d)"
    >
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.situacao === 'aberta' ? 'orange' : 'positive'">{{ props.row.situacao === 'aberta' ? 'Aberta' : 'Confirmada' }}</q-badge>
          <q-badge v-if="props.row.retificadora" outline color="primary" class="q-ml-xs">Retificadora</q-badge>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarMoeda } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()
const aba = ref(rota.query.aba === 'devolucoes' ? 'devolucoes' : 'transferencias')
const documentos = ref([])
const carregando = ref(true)

const colunas = [
  { name: 'numero', label: 'Nº', field: 'numero', align: 'left' },
  { name: 'data', label: 'Data', field: (d) => d.confirmada_em ?? d.criado_em, format: formatarDataHora, align: 'left' },
  { name: 'representante', label: 'Representante', field: (d) => `${d.representante.codigo} · ${d.representante.cliente.nome}`, align: 'left' },
  { name: 'itens', label: 'Produtos', field: (d) => d.itens.length, align: 'right' },
  { name: 'total', label: 'Total', field: 'total', format: formatarMoeda, align: 'right' },
  { name: 'situacao', label: 'Situação', field: 'situacao', align: 'left' },
  { name: 'atendida_por', label: 'Atendido por', field: (d) => d.atendida_por.nome, align: 'left' },
]

function abrir(d) {
  const devolucao = aba.value === 'devolucoes'
  const editar = d.situacao === 'aberta' && sessao.pode('consignacao.transferir')
  const nome = editar ? (devolucao ? 'devolucao' : 'transferencia') : devolucao ? 'comprovante-devolucao' : 'comprovante-transferencia'
  roteador.push({ name: nome, params: { id: d.id } })
}

async function carregar() {
  carregando.value = true
  try {
    documentos.value = (await api.get(`/consignacao/${aba.value}`)).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function trocarAba() {
  roteador.replace({ query: aba.value === 'devolucoes' ? { aba: 'devolucoes' } : {} })
  carregar()
}

onMounted(carregar)
</script>
