<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Formas de pagamento</div>
      <q-btn color="primary" unelevated no-caps icon="add" label="Nova forma" @click="abrir()" />
    </div>
    <div class="text-caption text-suave q-mb-md">
      Valem para todas as lojas. O desconto da forma entra sozinho na venda; acima das parcelas sem autorização, a venda pede a gerência.
    </div>

    <q-table
      flat
      bordered
      :rows="formas"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 0 }"
      hide-pagination
      no-data-label="Nenhuma forma cadastrada"
      loading-label="Carregando..."
      class="tabela-clicavel"
      @row-click="(_, f) => abrir(f)"
    >
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.ativo ? 'positive' : 'grey'">{{ props.row.ativo ? 'Ativa' : 'Inativa' }}</q-badge>
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="dialogo">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="salvar">
          <q-card-section class="piki-titulo">{{ editando.id ? 'Editar forma' : 'Nova forma' }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-input v-model="editando.nome" outlined autofocus label="Nome *" maxlength="30" :rules="[(v) => !!v?.trim() || 'Informe o nome']" />
            <q-select v-model="editando.tipo" outlined label="Tipo *" :options="tipos" option-value="codigo" option-label="nome" emit-value map-options />
            <div class="row q-col-gutter-sm">
              <q-input v-model="editando.desconto" outlined type="number" step="0.01" min="0" suffix="%" label="Desconto" class="col-6" />
              <q-input v-model.number="editando.ordem" outlined type="number" label="Ordem na venda" class="col-6" />
              <q-input v-model.number="editando.parcelas" outlined type="number" min="1" label="Parcelas (máximo)" class="col-6" />
              <q-input v-model.number="editando.parcelas_sem_autorizacao" outlined type="number" min="1" label="Sem autorização até" class="col-6" />
              <q-input v-model.number="editando.intervalo" outlined type="number" min="0" suffix="dias" label="Intervalo das parcelas" class="col-6" />
            </div>
            <q-toggle v-model="editando.ativo" label="Ativa" />
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
import { onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'

const $q = useQuasar()
const formas = ref([])
const tipos = ref([])
const carregando = ref(false)
const dialogo = ref(false)
const salvando = ref(false)
const editando = ref({})

const colunas = [
  { name: 'nome', label: 'Forma', field: 'nome', align: 'left' },
  { name: 'tipo', label: 'Tipo', field: (f) => tipos.value.find((t) => t.codigo === f.tipo)?.nome ?? f.tipo, align: 'left' },
  { name: 'desconto', label: 'Desconto', field: 'desconto', align: 'right', format: (v) => `${Number(v).toLocaleString('pt-BR')}%` },
  { name: 'parcelas', label: 'Parcelas', align: 'right', field: (f) => (f.parcelas > 1 ? `até ${f.parcelas} (${f.parcelas_sem_autorizacao} sem autorização)` : '1') },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

async function carregar() {
  carregando.value = true
  try {
    const [f, t] = await Promise.all([api.get('/formas-pagamento'), api.get('/formas-pagamento/tipos')])
    formas.value = f.data
    tipos.value = t.data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function abrir(forma) {
  editando.value = forma
    ? { ...forma }
    : { nome: '', tipo: 'dinheiro', desconto: '0', parcelas: 1, parcelas_sem_autorizacao: 1, intervalo: 30, ordem: formas.value.length + 1, ativo: true }
  dialogo.value = true
}

async function salvar() {
  salvando.value = true
  try {
    const { id, codigo_nfce, ...dados } = editando.value
    dados.desconto = String(dados.desconto || '0')
    await (id ? api.put(`/formas-pagamento/${id}`, dados) : api.post('/formas-pagamento', dados))
    dialogo.value = false
    await carregar()
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

onMounted(carregar)
</script>
