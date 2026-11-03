<template>
  <!-- inutilização (D29), como no VB6: busca os números pulados da série e pede à SEFAZ que não valham mais -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'notas' }" />
      <div class="piki-titulo col">Inutilizar números</div>
    </div>

    <section class="cartao q-pa-md q-mb-md">
      <div class="row q-col-gutter-sm items-center">
        <q-select
          v-model="serie"
          :options="series"
          :option-label="(s) => `Série ${s.serie} (${s.modelo === '65' ? 'NFC-e' : 'NF-e'}, até o nº ${s.ultimo})`"
          outlined
          dense
          label="Série"
          class="col-12 col-sm-5"
        />
        <q-input v-model="desde" type="date" outlined dense stack-label label="Notas emitidas desde" class="col-6 col-sm-3" />
        <div class="col-auto">
          <q-btn unelevated no-caps color="primary" icon="search" label="Buscar lacunas" :disable="!serie || !desde" :loading="buscando" @click="buscar" />
        </div>
      </div>

      <template v-if="lacunas">
        <q-banner v-if="lacunas.pendentes.length" rounded class="bg-orange-1 q-mt-md">
          Notas sem resposta da SEFAZ nesta série: {{ lacunas.pendentes.join(', ') }}. Consulte-as antes, em Notas fiscais.
        </q-banner>
        <div v-if="!lacunas.faixas.length" class="text-suave q-mt-md">Nenhum número pulado nesta série desde esta data.</div>
        <q-list v-else bordered separator class="q-mt-md lista-faixas">
          <q-item v-for="f in lacunas.faixas" :key="f.inicial" clickable :active="f.inicial === inicial && f.final === final" @click="escolher(f)">
            <q-item-section>{{ f.inicial === f.final ? `Número ${f.inicial}` : `Do ${f.inicial} ao ${f.final}` }}</q-item-section>
            <q-item-section side>{{ f.final - f.inicial + 1 }} {{ f.final === f.inicial ? 'número' : 'números' }}</q-item-section>
          </q-item>
        </q-list>
      </template>

      <div class="row q-col-gutter-sm items-start q-mt-md">
        <q-input v-model.number="inicial" type="number" outlined dense label="Do número" class="col-6 col-sm-2" />
        <q-input v-model.number="final" type="number" outlined dense label="Até o número" class="col-6 col-sm-2" />
        <q-input v-model="justificativa" outlined dense label="Justificativa (de 15 a 255 letras)" maxlength="255" counter class="col-12 col-sm" />
        <div class="col-auto">
          <q-btn unelevated no-caps color="negative" icon="block" label="Inutilizar" :disable="!podeInutilizar" :loading="enviando" @click="inutilizar" />
        </div>
      </div>
    </section>

    <q-table
      flat
      bordered
      title="Inutilizações feitas"
      :rows="feitas"
      :columns="colunas"
      row-key="id"
      :pagination="{ rowsPerPage: 20 }"
      no-data-label="Nenhuma inutilização"
    />
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora } from '@/servicos/formatos'

const $q = useQuasar()
const series = ref([])
const serie = ref(null)
const hoje = new Date()
const desde = ref(new Date(hoje.getFullYear(), hoje.getMonth(), 1).toLocaleDateString('sv-SE'))
const lacunas = ref(null)
const buscando = ref(false)
const inicial = ref(null)
const final = ref(null)
const justificativa = ref('')
const enviando = ref(false)
const feitas = ref([])

const podeInutilizar = computed(() => serie.value && inicial.value > 0 && final.value >= inicial.value && justificativa.value.trim().length >= 15)

const colunas = [
  { name: 'serie', label: 'Série', field: 'serie', align: 'left' },
  { name: 'faixa', label: 'Números', field: (i) => (i.inicial === i.final ? `${i.inicial}` : `${i.inicial} a ${i.final}`), align: 'left' },
  { name: 'justificativa', label: 'Justificativa', field: 'justificativa', align: 'left' },
  { name: 'protocolo', label: 'Protocolo', field: 'protocolo', align: 'left' },
  { name: 'homologada_em', label: 'Em', field: 'homologada_em', format: formatarDataHora, align: 'left' },
  { name: 'feita_por', label: 'Por', field: (i) => i.feita_por.nome, align: 'left' },
]

function escolher(faixa) {
  inicial.value = faixa.inicial
  final.value = faixa.final
}

async function buscar() {
  buscando.value = true
  try {
    lacunas.value = (await api.get('/notas/lacunas', { params: { modelo: serie.value.modelo, serie: serie.value.serie, desde: desde.value } })).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    buscando.value = false
  }
}

function inutilizar() {
  const faixa = inicial.value === final.value ? `o número ${inicial.value}` : `os números ${inicial.value} a ${final.value}`
  $q.dialog({
    title: 'Inutilizar números',
    message: `Pedir à SEFAZ a inutilização de ${faixa} da série ${serie.value.serie}? Não se desfaz.`,
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Inutilizar', color: 'negative' },
  }).onOk(async () => {
    enviando.value = true
    try {
      const pedido = { modelo: serie.value.modelo, serie: serie.value.serie, inicial: inicial.value, final: final.value, justificativa: justificativa.value.trim() }
      const feita = (await api.post('/notas/inutilizacoes', pedido)).data
      feitas.value = [feita, ...feitas.value]
      $q.notify({ type: 'positive', message: `Números inutilizados. Protocolo ${feita.protocolo}` })
      inicial.value = final.value = null
      await buscar()
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e), timeout: 8000 })
    } finally {
      enviando.value = false
    }
  })
}

onMounted(async () => {
  try {
    const [s, f] = await Promise.all([api.get('/notas/series'), api.get('/notas/inutilizacoes')])
    series.value = s.data
    serie.value = s.data[0] ?? null
    feitas.value = f.data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
})
</script>

<style scoped>
.lista-faixas {
  max-width: 420px;
}
</style>
