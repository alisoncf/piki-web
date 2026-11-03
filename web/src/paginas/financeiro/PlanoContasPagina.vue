<template>
  <!-- as contas de receita e de despesa (D28): para onde foi, ou de onde veio, o dinheiro -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Plano de contas</div>
      <q-btn v-if="podeEditar" color="primary" unelevated no-caps icon="add" label="Nova conta" @click="abrir()" />
    </div>

    <div class="row q-col-gutter-md">
      <div v-for="t in TIPOS" :key="t.value" class="col-12 col-md-6">
        <q-table
          flat
          bordered
          :title="t.titulo"
          :rows="contas.filter((c) => c.tipo === t.value)"
          :columns="colunas"
          row-key="id"
          :loading="carregando"
          :pagination="{ rowsPerPage: 0 }"
          hide-pagination
          no-data-label="Nenhuma conta"
          :class="{ 'tabela-clicavel': podeEditar }"
          @row-click="(_, c) => podeEditar && abrir(c)"
        >
          <template #body-cell-situacao="props">
            <q-td :props="props">
              <q-badge :color="props.row.ativo ? 'positive' : 'grey'">{{ props.row.ativo ? 'Ativa' : 'Inativa' }}</q-badge>
            </q-td>
          </template>
        </q-table>
      </div>
    </div>

    <q-dialog v-model="dialogo">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="salvar">
          <q-card-section class="piki-titulo">{{ editando.id ? 'Editar conta' : 'Nova conta' }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-btn-toggle v-model="editando.tipo" no-caps unelevated toggle-color="primary" :options="TIPOS.map((t) => ({ label: t.nome, value: t.value }))" />
            <q-input v-model="editando.nome" outlined autofocus label="Nome *" maxlength="60" :rules="[(v) => !!v?.trim() || 'Informe o nome']" />
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
import { computed, onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const TIPOS = [
  { value: 'receita', nome: 'Receita', titulo: 'Receitas' },
  { value: 'despesa', nome: 'Despesa', titulo: 'Despesas' },
]

const $q = useQuasar()
const sessao = useSessaoStore()
const contas = ref([])
const carregando = ref(true)
const dialogo = ref(false)
const salvando = ref(false)
const editando = ref({})
const podeEditar = computed(() => sessao.pode('financeiro.plano'))

const colunas = [
  { name: 'nome', label: 'Conta', field: 'nome', align: 'left' },
  { name: 'situacao', label: '', field: 'ativo', align: 'right' },
]

async function carregar() {
  carregando.value = true
  try {
    contas.value = (await api.get('/plano-contas')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function abrir(conta) {
  editando.value = conta ? { ...conta } : { tipo: 'despesa', nome: '', ativo: true }
  dialogo.value = true
}

async function salvar() {
  salvando.value = true
  try {
    const { id, ...dados } = editando.value
    await (id ? api.put(`/plano-contas/${id}`, dados) : api.post('/plano-contas', dados))
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
