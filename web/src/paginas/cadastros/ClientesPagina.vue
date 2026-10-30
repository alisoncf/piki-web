<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Clientes</div>
      <q-btn
        v-if="sessao.pode('clientes.editar')"
        color="primary"
        unelevated
        no-caps
        icon="add"
        label="Novo cliente"
        :to="{ name: 'cliente-novo' }"
      />
    </div>

    <!-- são dezenas de milhares de clientes: a busca e a paginação são feitas pela API -->
    <q-table
      v-model:pagination="paginacao"
      flat
      bordered
      :rows="clientes"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :rows-per-page-options="[20, 50, 100]"
      no-data-label="Nenhum cliente encontrado"
      loading-label="Carregando..."
      rows-per-page-label="Por página"
      class="tabela-clicavel"
      @request="aoPaginar"
      @row-click="(_, c) => $router.push({ name: 'cliente', params: { id: c.id } })"
    >
      <template #top>
        <div class="row items-center q-gutter-md full-width">
          <q-input
            v-model="busca"
            dense
            outlined
            debounce="400"
            placeholder="Nome, CPF/CNPJ ou telefone"
            clearable
            autofocus
            class="col-12 col-sm"
          >
            <template #prepend><q-icon name="search" /></template>
          </q-input>
          <q-toggle v-model="soBloqueados" label="Só bloqueados" />
        </div>
      </template>
      <template #body-cell-nome="props">
        <q-td :props="props">
          <div class="text-weight-medium">{{ props.row.nome }}</div>
          <div v-if="props.row.setor" class="text-caption text-suave">{{ props.row.setor.nome }}</div>
        </q-td>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge v-if="props.row.bloqueado" color="negative" class="q-mr-xs">Bloqueado</q-badge>
          <q-badge v-if="props.row.credito_suspenso" color="warning" text-color="dark">Crédito suspenso</q-badge>
          <q-badge v-if="!props.row.bloqueado && !props.row.credito_suspenso" color="positive">Liberado</q-badge>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onMounted, ref, watch } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDocumento } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const sessao = useSessaoStore()

const clientes = ref([])
const carregando = ref(false)
const busca = ref('')
const soBloqueados = ref(false)
const paginacao = ref({ page: 1, rowsPerPage: 20, rowsNumber: 0 })

const colunas = [
  { name: 'nome', label: 'Nome', field: 'nome', align: 'left' },
  { name: 'cpf_cnpj', label: 'CPF/CNPJ', field: 'cpf_cnpj', align: 'left', format: (v) => (v ? formatarDocumento(v) : '') },
  { name: 'bairro', label: 'Bairro', field: 'bairro', align: 'left' },
  { name: 'cidade', label: 'Cidade', field: 'cidade', align: 'left' },
  { name: 'situacao', label: 'Situação', field: 'bloqueado', align: 'left' },
]

async function carregar() {
  carregando.value = true
  const { page, rowsPerPage } = paginacao.value
  try {
    const params = { limite: rowsPerPage, deslocamento: (page - 1) * rowsPerPage }
    if (busca.value?.trim()) params.busca = busca.value.trim()
    if (soBloqueados.value) params.bloqueado = true
    const { data } = await api.get('/clientes', { params })
    clientes.value = data.itens
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

watch([busca, soBloqueados], () => {
  paginacao.value = { ...paginacao.value, page: 1 }
  carregar()
})

onMounted(carregar)
</script>
