<template>
  <!-- as transferências do consignado da loja (D30) -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Transferências</div>
      <q-btn v-if="sessao.pode('consignacao.transferir')" color="primary" unelevated no-caps icon="add" label="Nova transferência" :to="{ name: 'transferencia-nova' }" />
    </div>

    <q-table
      flat
      bordered
      :rows="transferencias"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 30 }"
      no-data-label="Nenhuma transferência"
      class="tabela-clicavel"
      @row-click="(_, t) => abrir(t)"
    >
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.situacao === 'aberta' ? 'orange' : 'positive'">{{ props.row.situacao === 'aberta' ? 'Aberta' : 'Confirmada' }}</q-badge>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarMoeda } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const roteador = useRouter()
const sessao = useSessaoStore()
const transferencias = ref([])
const carregando = ref(true)

const colunas = [
  { name: 'numero', label: 'Nº', field: 'numero', align: 'left' },
  { name: 'data', label: 'Data', field: (t) => t.confirmada_em ?? t.criado_em, format: formatarDataHora, align: 'left' },
  { name: 'representante', label: 'Representante', field: (t) => `${t.representante.codigo} · ${t.representante.cliente.nome}`, align: 'left' },
  { name: 'itens', label: 'Produtos', field: (t) => t.itens.length, align: 'right' },
  { name: 'total', label: 'Total', field: 'total', format: formatarMoeda, align: 'right' },
  { name: 'situacao', label: 'Situação', field: 'situacao', align: 'left' },
  { name: 'atendida_por', label: 'Atendido por', field: (t) => t.atendida_por.nome, align: 'left' },
]

function abrir(t) {
  const aberta = t.situacao === 'aberta' && sessao.pode('consignacao.transferir')
  roteador.push({ name: aberta ? 'transferencia' : 'comprovante-transferencia', params: { id: t.id } })
}

onMounted(async () => {
  try {
    transferencias.value = (await api.get('/consignacao/transferencias')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>
