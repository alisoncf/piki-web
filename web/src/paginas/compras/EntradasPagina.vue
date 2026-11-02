<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Entrada de notas</div>
      <q-btn
        v-if="sessao.pode('entradas.lancar')"
        color="primary"
        unelevated
        no-caps
        icon="upload_file"
        label="Carregar XML"
        :loading="carregandoXml"
        @click="seletor.click()"
      />
      <input ref="seletor" type="file" accept=".xml,application/xml,text/xml" hidden @change="carregarXml" />
    </div>

    <q-table
      v-model:pagination="paginacao"
      flat
      bordered
      :rows="notas"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :rows-per-page-options="[20, 50, 100]"
      rows-per-page-label="Por página"
      no-data-label="Nenhuma nota de entrada nesta loja"
      loading-label="Carregando..."
      class="tabela-clicavel"
      @request="aoPaginar"
      @row-click="(_, n) => $router.push({ name: 'entrada', params: { id: n.id } })"
    >
      <template #top>
        <div class="row items-center q-gutter-md full-width">
          <q-input v-model="busca" dense outlined debounce="300" placeholder="Fornecedor, número ou chave" clearable class="col-12 col-sm">
            <template #prepend><q-icon name="search" /></template>
          </q-input>
          <q-btn-toggle
            v-model="situacao"
            no-caps
            unelevated
            toggle-color="primary"
            :options="[{ label: 'Todas', value: null }, { label: 'Abertas', value: 'aberta' }, { label: 'Confirmadas', value: 'confirmada' }]"
          />
        </div>
      </template>
      <template #body-cell-fornecedor="props">
        <q-td :props="props">
          <div class="text-weight-medium">{{ props.row.fornecedor.nome_fantasia || props.row.fornecedor.nome }}</div>
          <div class="text-caption text-suave">{{ formatarDocumento(props.row.fornecedor.cpf_cnpj) }}</div>
        </q-td>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.situacao === 'confirmada' ? 'positive' : 'warning'">
            {{ props.row.situacao === 'confirmada' ? 'Confirmada' : 'Aberta' }}
          </q-badge>
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
import { formatarDataHora, formatarDocumento, formatarMoeda } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const roteador = useRouter()
const sessao = useSessaoStore()

const notas = ref([])
const carregando = ref(false)
const carregandoXml = ref(false)
const seletor = ref(null)
const busca = ref('')
const situacao = ref(null)
const paginacao = ref({ page: 1, rowsPerPage: 20, rowsNumber: 0 })

const colunas = [
  { name: 'numero', label: 'Nota', field: (n) => `${n.numero}/${n.serie}`, align: 'left' },
  { name: 'emissao', label: 'Emissão', field: 'data_emissao', align: 'left', format: (v) => formatarDataHora(v).slice(0, 10) },
  { name: 'fornecedor', label: 'Fornecedor', field: (n) => n.fornecedor.nome, align: 'left' },
  { name: 'valor', label: 'Valor', field: 'valor_total', align: 'right', format: formatarMoeda },
  { name: 'situacao', label: 'Situação', field: 'situacao', align: 'left' },
]

async function carregar() {
  carregando.value = true
  const { page, rowsPerPage } = paginacao.value
  try {
    const params = { limite: rowsPerPage, deslocamento: (page - 1) * rowsPerPage }
    if (busca.value?.trim()) params.busca = busca.value.trim()
    if (situacao.value) params.situacao = situacao.value
    const { data } = await api.get('/entradas', { params })
    notas.value = data.itens
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

watch([busca, situacao], () => {
  paginacao.value = { ...paginacao.value, page: 1 }
  carregar()
})

onMounted(carregar)

async function carregarXml(evento) {
  const arquivo = evento.target.files?.[0]
  evento.target.value = '' // permite escolher o mesmo arquivo de novo
  if (!arquivo) return
  carregandoXml.value = true
  try {
    const { data } = await api.post('/entradas', arquivo, { headers: { 'Content-Type': 'application/xml' } })
    if (data.fornecedor_novo) {
      $q.notify({ type: 'info', message: `Fornecedor ${data.fornecedor.nome} cadastrado com os dados da nota`, timeout: 4000 })
    }
    await roteador.push({ name: 'entrada', params: { id: data.id } })
  } catch (e) {
    const existente = e.response?.headers?.['x-nota-id']
    if (e.response?.status === 409 && existente) {
      $q.notify({ type: 'warning', message: mensagemDeErro(e) })
      await roteador.push({ name: 'entrada', params: { id: existente } })
    } else {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  } finally {
    carregandoXml.value = false
  }
}
</script>
