<template>
  <!-- a natureza e o CFOP de cada operação que gera nota (D29): parametrizável, para conferir com o contador -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Naturezas das notas</div>
    </div>
    <div class="text-caption text-suave q-mb-md">
      A NF-e usa o CFOP de dentro do estado quando o cliente é de Goiás e o de fora quando não é. A NFC-e usa o CFOP do estoque de cada produto.
    </div>

    <q-table
      flat
      bordered
      :rows="operacoes"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 0 }"
      hide-pagination
      :class="{ 'tabela-clicavel': podeEditar }"
      @row-click="(_, o) => podeEditar && abrir(o)"
    />

    <q-dialog v-model="dialogo">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="salvar">
          <q-card-section class="piki-titulo">{{ USOS[editando.uso] }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-input v-model="editando.natureza" outlined autofocus label="Natureza da operação *" maxlength="60" :rules="[(v) => !!v?.trim() || 'Informe a natureza']" />
            <q-btn-toggle v-model="editando.tipo" no-caps unelevated toggle-color="primary" :options="TIPOS" />
            <q-select v-model="editando.finalidade" :options="FINALIDADES" emit-value map-options outlined label="Finalidade" />
            <div class="row q-col-gutter-sm">
              <q-input v-model="editando.cfop_estado" outlined label="CFOP dentro do estado *" mask="####" class="col-6" :rules="[cfopValido]" />
              <q-input v-model="editando.cfop_fora" outlined label="CFOP para fora *" mask="####" class="col-6" :rules="[cfopValido]" />
            </div>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Salvar" :loading="salvando" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const USOS = { venda: 'Venda', remessa: 'Remessa ao representante', retorno_remessa: 'Retorno de remessa', devolucao: 'Devolução' }
const TIPOS = [{ label: 'Saída', value: '1' }, { label: 'Entrada', value: '0' }]
const FINALIDADES = [
  { label: 'Normal', value: '1' }, { label: 'Complementar', value: '2' }, { label: 'Ajuste', value: '3' }, { label: 'Devolução', value: '4' },
]

const $q = useQuasar()
const sessao = useSessaoStore()
const podeEditar = computed(() => sessao.pode('notas.configurar'))
const operacoes = ref([])
const carregando = ref(true)
const dialogo = ref(false)
const editando = ref({})
const salvando = ref(false)

const colunas = [
  { name: 'uso', label: 'Operação', field: (o) => USOS[o.uso], align: 'left' },
  { name: 'natureza', label: 'Natureza', field: 'natureza', align: 'left' },
  { name: 'tipo', label: 'Tipo', field: (o) => TIPOS.find((t) => t.value === o.tipo)?.label, align: 'left' },
  { name: 'finalidade', label: 'Finalidade', field: (o) => FINALIDADES.find((f) => f.value === o.finalidade)?.label, align: 'left' },
  { name: 'cfop_estado', label: 'CFOP no estado', field: 'cfop_estado' },
  { name: 'cfop_fora', label: 'CFOP para fora', field: 'cfop_fora' },
]

function cfopValido(v) {
  return /^\d{4}$/.test(v ?? '') || 'Quatro dígitos'
}

function abrir(operacao) {
  editando.value = { ...operacao }
  dialogo.value = true
}

async function salvar() {
  salvando.value = true
  try {
    const { id, uso, ...dados } = editando.value
    const salva = (await api.put(`/notas/operacoes/${id}`, { ...dados, natureza: dados.natureza.trim() })).data
    operacoes.value = operacoes.value.map((o) => (o.id === id ? salva : o))
    dialogo.value = false
    $q.notify({ type: 'positive', message: `${USOS[uso]}: salva` })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

onMounted(async () => {
  try {
    operacoes.value = (await api.get('/notas/operacoes')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>
