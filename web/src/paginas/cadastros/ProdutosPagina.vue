<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Produtos</div>
      <q-btn
        v-if="sessao.pode('produtos.editar')"
        color="primary"
        unelevated
        no-caps
        icon="add"
        label="Novo produto"
        :to="{ name: 'produto-novo' }"
      />
    </div>

    <q-table
      v-model:pagination="paginacao"
      flat
      bordered
      :rows="produtos"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :rows-per-page-options="[20, 50, 100]"
      rows-per-page-label="Por página"
      no-data-label="Nenhum produto encontrado"
      loading-label="Carregando..."
      class="tabela-clicavel"
      @request="aoPaginar"
      @row-click="(_, p) => $router.push({ name: 'produto', params: { id: p.id } })"
    >
      <template #top>
        <div class="row items-center q-gutter-md full-width">
          <q-input
            v-model="busca"
            dense
            outlined
            debounce="300"
            placeholder="Código, código de barras ou palavras do nome"
            clearable
            autofocus
            class="col-12 col-sm"
          >
            <template #prepend><q-icon name="search" /></template>
          </q-input>
          <q-select
            v-model="secaoId"
            dense
            outlined
            clearable
            label="Seção"
            :options="secoes"
            option-value="id"
            option-label="nome"
            emit-value
            map-options
            class="col-12 col-sm-3"
          />
          <q-toggle v-model="soAtivos" label="Só ativos" />
        </div>
      </template>
      <template #body-cell-nome="props">
        <q-td :props="props">
          <div class="text-weight-medium">{{ props.row.nome }}</div>
          <div class="text-caption text-suave">
            {{ [props.row.subsecao?.secao.nome, props.row.subsecao?.nome].filter(Boolean).join(' › ') }}
            <template v-if="props.row.marca"> · {{ props.row.marca.nome }}</template>
          </div>
        </q-td>
      </template>
      <template #body-cell-preco="props">
        <q-td :props="props">
          <template v-if="props.row.preco_queima">
            <div class="text-caption text-suave" style="text-decoration: line-through">{{ formatarMoeda(props.row.preco_venda) }}</div>
            <div class="text-weight-medium text-negative">{{ formatarMoeda(props.row.preco_queima) }} <q-badge color="negative">Queima</q-badge></div>
          </template>
          <template v-else>{{ formatarMoeda(props.row.preco_venda) }}</template>
        </q-td>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.ativo ? 'positive' : 'grey'">{{ props.row.ativo ? 'Ativo' : 'Inativo' }}</q-badge>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onMounted, ref, watch } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCodigoProduto, formatarMoeda } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const sessao = useSessaoStore()

const produtos = ref([])
const secoes = ref([])
const carregando = ref(false)
const busca = ref('')
const secaoId = ref(null)
const soAtivos = ref(true)
const paginacao = ref({ page: 1, rowsPerPage: 20, rowsNumber: 0 })

const colunas = [
  { name: 'codigo', label: 'Código', field: 'codigo', align: 'left', format: formatarCodigoProduto },
  { name: 'nome', label: 'Produto', field: 'nome', align: 'left' },
  { name: 'fornecedor', label: 'Fornecedor', field: 'fornecedor', align: 'left' },
  { name: 'unidade', label: 'Un.', field: 'unidade', align: 'center' },
  { name: 'preco', label: 'Preço', field: 'preco_venda', align: 'right' },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

// são milhares: a busca e a paginação são feitas na API
async function carregar() {
  carregando.value = true
  const { page, rowsPerPage } = paginacao.value
  try {
    const params = { limite: rowsPerPage, deslocamento: (page - 1) * rowsPerPage }
    if (busca.value?.trim()) params.busca = busca.value.trim()
    if (secaoId.value) params.secao_id = secaoId.value
    if (soAtivos.value) params.ativo = true
    const { data } = await api.get('/produtos', { params })
    produtos.value = data.itens
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

watch([busca, secaoId, soAtivos], () => {
  paginacao.value = { ...paginacao.value, page: 1 }
  carregar()
})

onMounted(async () => {
  carregar()
  try {
    secoes.value = (await api.get('/secoes')).data
  } catch {
    /* sem o filtro de seção */
  }
})
</script>
