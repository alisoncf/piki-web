<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Cargos</div>
      <q-btn v-if="podeEditar" color="primary" unelevated no-caps icon="add" label="Novo cargo" @click="abrir()" />
    </div>

    <q-table
      flat
      bordered
      :rows="cargos"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 0 }"
      hide-pagination
      no-data-label="Nenhum cargo cadastrado"
      loading-label="Carregando..."
      :class="{ 'tabela-clicavel': podeEditar }"
      @row-click="(_, c) => podeEditar && abrir(c)"
    >
      <template #body-cell-papeis="props">
        <q-td :props="props">
          <q-badge v-if="props.row.vende" color="primario-claro" text-color="primary" class="q-mr-xs">Vende</q-badge>
          <q-badge v-if="props.row.cobra" color="primario-claro" text-color="primary">Cobra</q-badge>
        </q-td>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.ativo ? 'positive' : 'grey'">{{ props.row.ativo ? 'Ativo' : 'Inativo' }}</q-badge>
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="dialogo">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="salvar">
          <q-card-section class="piki-titulo">{{ editando.id ? 'Editar cargo' : 'Novo cargo' }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-input
              v-model="editando.nome"
              outlined
              autofocus
              label="Nome *"
              maxlength="40"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            />
            <q-toggle v-model="editando.vende" label="Vende (aparece na escolha de vendedor)" />
            <q-toggle v-model="editando.cobra" label="Cobra (aparece na escolha de cobrador)" />
            <q-toggle v-model="editando.ativo" label="Ativo" />
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

const $q = useQuasar()
const sessao = useSessaoStore()
const podeEditar = computed(() => sessao.pode('funcionarios.editar'))

const cargos = ref([])
const carregando = ref(false)
const dialogo = ref(false)
const salvando = ref(false)
const editando = ref({})

const colunas = [
  { name: 'nome', label: 'Nome', field: 'nome', align: 'left', sortable: true },
  { name: 'papeis', label: 'Na venda e cobrança', field: 'vende', align: 'left' },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

async function carregar() {
  carregando.value = true
  try {
    cargos.value = (await api.get('/cargos')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function abrir(cargo) {
  editando.value = cargo ? { ...cargo } : { nome: '', vende: false, cobra: false, ativo: true }
  dialogo.value = true
}

async function salvar() {
  salvando.value = true
  try {
    const { id, ...dados } = editando.value
    await (id ? api.put(`/cargos/${id}`, dados) : api.post('/cargos', dados))
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
