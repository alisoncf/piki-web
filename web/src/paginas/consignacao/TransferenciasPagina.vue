<template>
  <!-- as transferências, as devoluções e os acertos do consignado da loja (D30) -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Consignado</div>
      <template v-if="sessao.pode('consignacao.transferir')">
        <q-btn flat no-caps color="primary" icon="move_down" label="Nova devolução" :to="{ name: 'devolucao-nova' }" />
        <q-btn color="primary" unelevated no-caps icon="move_up" label="Nova transferência" class="q-ml-sm" :to="{ name: 'transferencia-nova' }" />
      </template>
      <q-btn v-if="sessao.pode('consignacao.acertar')" color="primary" unelevated no-caps icon="handshake" label="Novo acerto" class="q-ml-sm" :to="{ name: 'acerto-novo' }" />
    </div>

    <q-tabs v-model="aba" no-caps align="left" active-color="primary" class="q-mb-sm" @update:model-value="trocarAba">
      <q-tab name="transferencias" label="Transferências" />
      <q-tab name="devolucoes" label="Devoluções" />
      <q-tab name="acertos" label="Acertos" />
    </q-tabs>

    <q-table
      flat
      bordered
      :rows="documentos"
      :columns="colunasDaAba"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 30 }"
      :no-data-label="{ devolucoes: 'Nenhuma devolução', acertos: 'Nenhum acerto' }[aba] ?? 'Nenhuma transferência'"
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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarMoeda } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()
const ABAS = ['transferencias', 'devolucoes', 'acertos']
const aba = ref(ABAS.includes(rota.query.aba) ? rota.query.aba : 'transferencias')
// a tela de cada documento: a aberta para continuar, a confirmada para o comprovante
const TELAS = {
  transferencias: { editar: 'transferencia', comprovante: 'comprovante-transferencia', permissao: 'consignacao.transferir' },
  devolucoes: { editar: 'devolucao', comprovante: 'comprovante-devolucao', permissao: 'consignacao.transferir' },
  acertos: { editar: 'acerto', comprovante: 'comprovante-acerto', permissao: 'consignacao.acertar' },
}
const documentos = ref([])
const carregando = ref(true)

const colunas = [
  { name: 'numero', label: 'Nº', field: 'numero', align: 'left' },
  { name: 'data', label: 'Data', field: (d) => d.confirmada_em ?? d.criado_em, format: formatarDataHora, align: 'left' },
  { name: 'representante', label: 'Representante', field: (d) => `${d.representante.codigo} · ${d.representante.cliente.nome}`, align: 'left' },
  { name: 'itens', label: 'Produtos', field: (d) => d.itens.length, align: 'right' },
  { name: 'para', label: 'Para', field: (d) => (d.para ? (d.para === 'cliente' ? d.cliente?.nome ?? '' : 'Ele mesmo') : ''), align: 'left' },
  { name: 'total', label: 'Total', field: (d) => d.valor ?? d.total, format: formatarMoeda, align: 'right' },
  { name: 'situacao', label: 'Situação', field: 'situacao', align: 'left' },
  { name: 'atendida_por', label: 'Atendido por', field: (d) => d.atendida_por.nome, align: 'left' },
]

const colunasDaAba = computed(() => colunas.filter((c) => c.name !== 'para' || aba.value === 'acertos'))

function abrir(d) {
  const tela = TELAS[aba.value]
  const editar = d.situacao === 'aberta' && sessao.pode(tela.permissao)
  roteador.push({ name: editar ? tela.editar : tela.comprovante, params: { id: d.id } })
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
  roteador.replace({ query: aba.value === 'transferencias' ? {} : { aba: aba.value } })
  carregar()
}

onMounted(carregar)
</script>
