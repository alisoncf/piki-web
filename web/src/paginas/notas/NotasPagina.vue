<template>
  <!-- as notas emitidas pela loja (D29): consultar na SEFAZ, reimprimir, baixar o XML, cancelar -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Notas fiscais</div>
      <q-btn v-if="sessao.pode('notas.inutilizar')" flat no-caps color="primary" icon="block" label="Inutilizar números" :to="{ name: 'inutilizar-numeros' }" />
    </div>

    <div class="row q-col-gutter-sm q-mb-md items-center">
      <q-input v-model="filtros.inicio" type="date" outlined dense label="De" stack-label class="col-6 col-sm-auto" />
      <q-input v-model="filtros.fim" type="date" outlined dense label="Até" stack-label class="col-6 col-sm-auto" />
      <q-select v-model="filtros.situacao" :options="SITUACOES" emit-value map-options clearable outlined dense label="Situação" class="col-12 col-sm-3" />
      <q-input v-model.number="filtros.numero" type="number" outlined dense clearable label="Número" class="col-6 col-sm-2" />
      <div class="col-auto"><q-btn unelevated no-caps color="primary" icon="search" label="Buscar" @click="buscar" /></div>
    </div>

    <q-table
      flat
      bordered
      :rows="notas"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 50 }"
      no-data-label="Nenhuma nota nestes filtros"
    >
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="COR[props.row.situacao]">{{ NOME[props.row.situacao] }}</q-badge>
          <q-badge v-if="props.row.ambiente === '2'" outline color="orange" class="q-ml-xs">Homologação</q-badge>
          <div v-if="props.row.motivo_retorno && props.row.situacao !== 'autorizada'" class="text-caption text-suave ellipsis motivo">
            {{ props.row.codigo_retorno }} {{ props.row.motivo_retorno }}
          </div>
        </q-td>
      </template>
      <template #body-cell-acoes="props">
        <q-td :props="props" class="text-right">
          <q-btn v-if="props.row.venda_id" flat dense no-caps icon="receipt" label="DANFE" :to="{ name: 'nfce-venda', params: { id: props.row.venda_id } }" />
          <q-btn flat dense no-caps icon="download" label="XML" @click="baixarXml(props.row)" />
          <q-btn v-if="podeEmitir && !['cancelada', 'inutilizada'].includes(props.row.situacao)" flat dense no-caps icon="travel_explore" label="Consultar" @click="consultar(props.row)" />
          <q-btn v-if="podeCancelar && props.row.situacao === 'autorizada'" flat dense no-caps color="negative" icon="block" label="Cancelar" @click="cancelar(props.row)" />
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarMoeda } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const NOME = { pendente: 'Pendente', rejeitada: 'Rejeitada', autorizada: 'Autorizada', cancelada: 'Cancelada', denegada: 'Denegada', inutilizada: 'Inutilizada' }
const COR = { pendente: 'orange', rejeitada: 'negative', autorizada: 'positive', cancelada: 'grey', denegada: 'negative', inutilizada: 'grey' }
const SITUACOES = Object.entries(NOME).map(([value, label]) => ({ value, label }))

const $q = useQuasar()
const sessao = useSessaoStore()
const podeEmitir = computed(() => sessao.pode('notas.emitir') || sessao.pode('caixa.operar'))
const podeCancelar = computed(() => sessao.pode('notas.cancelar'))

const hoje = new Date().toLocaleDateString('sv-SE')
const filtros = ref({ inicio: hoje, fim: hoje, situacao: null, numero: null })
const notas = ref([])
const carregando = ref(false)

const colunas = [
  { name: 'numero', label: 'NFC-e', field: (n) => `${n.numero} · série ${n.serie}`, align: 'left' },
  { name: 'emitida_em', label: 'Emissão', field: 'emitida_em', format: formatarDataHora, align: 'left' },
  { name: 'valor', label: 'Valor', field: 'valor', format: formatarMoeda, align: 'right' },
  { name: 'situacao', label: 'Situação', field: 'situacao', align: 'left' },
  { name: 'emitida_por', label: 'Por', field: (n) => n.emitida_por.nome, align: 'left' },
  { name: 'acoes', label: '', field: 'id' },
]

async function buscar() {
  carregando.value = true
  try {
    const params = Object.fromEntries(Object.entries(filtros.value).filter(([, v]) => v !== null && v !== ''))
    notas.value = (await api.get('/notas', { params })).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function trocar(nota) {
  notas.value = notas.value.map((n) => (n.id === nota.id ? nota : n))
}

async function baixarXml(nota) {
  try {
    const { data } = await api.get(`/notas/${nota.id}/xml`, { responseType: 'blob' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(data)
    link.download = `${nota.chave}.xml`
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

async function consultar(nota) {
  try {
    const atualizada = (await api.post(`/notas/${nota.id}/consultar`)).data
    trocar(atualizada)
    $q.notify({ type: 'info', message: `SEFAZ: ${atualizada.codigo_retorno} - ${atualizada.motivo_retorno}` })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

function cancelar(nota) {
  $q.dialog({
    title: `Cancelar a NFC-e ${nota.numero}`,
    message: 'O cancelamento vai para a SEFAZ e não se desfaz. A venda continua como está. Justificativa (de 15 a 255 letras):',
    prompt: { model: '', type: 'text', isValid: (v) => v.trim().length >= 15 && v.trim().length <= 255 },
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Cancelar a nota', color: 'negative' },
  }).onOk(async (justificativa) => {
    try {
      trocar((await api.post(`/notas/${nota.id}/cancelar`, { justificativa: justificativa.trim() })).data)
      $q.notify({ type: 'positive', message: `NFC-e ${nota.numero} cancelada` })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}

onMounted(buscar)
</script>

<style scoped>
.motivo {
  max-width: 320px;
}
</style>
