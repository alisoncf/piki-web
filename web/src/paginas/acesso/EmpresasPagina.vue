<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Empresas</div>
      <q-btn color="primary" unelevated no-caps icon="add" label="Nova empresa" :to="{ name: 'empresa-nova' }" />
    </div>

    <q-table
      flat
      bordered
      :rows="empresas"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 0 }"
      hide-pagination
      no-data-label="Nenhuma empresa cadastrada"
      loading-label="Carregando..."
      class="tabela-clicavel"
      @row-click="(_, e) => $router.push({ name: 'empresa', params: { id: e.id } })"
    >
      <template #body-cell-nome="props">
        <q-td :props="props">
          <q-avatar text-color="white" size="26px" font-size="12px" class="q-mr-sm" :style="{ background: props.row.tema.principal }">
            {{ props.row.codigo }}
          </q-avatar>
          <span class="text-weight-medium">{{ props.row.nome }}</span>
        </q-td>
      </template>
      <template #body-cell-ativa="props">
        <q-td :props="props">
          <q-badge :color="props.row.ativa ? 'positive' : 'grey-6'">{{ props.row.ativa ? 'Ativa' : 'Desativada' }}</q-badge>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCnpj } from '@/servicos/formatos'

const $q = useQuasar()

const empresas = ref([])
const carregando = ref(true)

const colunas = [
  { name: 'nome', label: 'Empresa', field: 'nome', align: 'left' },
  { name: 'razao_social', label: 'Razão social', field: 'razao_social', align: 'left' },
  { name: 'cnpj', label: 'CNPJ', field: 'cnpj', align: 'left', format: (v) => (v ? formatarCnpj(v) : '') },
  { name: 'cidade', label: 'Cidade', field: (e) => (e.cidade ? `${e.cidade.nome} - ${e.cidade.uf}` : ''), align: 'left' },
  { name: 'ativa', label: 'Situação', field: 'ativa', align: 'left' },
]

onMounted(async () => {
  try {
    empresas.value = (await api.get('/empresas')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>
