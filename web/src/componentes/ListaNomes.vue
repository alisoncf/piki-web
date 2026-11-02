<template>
  <!-- cadastro de lista simples, só com nome e situação (grupos de clientes, parentescos) -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">{{ titulo }}</div>
      <q-btn v-if="podeEditar" color="primary" unelevated no-caps icon="add" :label="`${feminino ? 'Nova' : 'Novo'} ${item}`" @click="abrir()" />
    </div>

    <q-table
      flat
      bordered
      :rows="itens"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 0 }"
      hide-pagination
      no-data-label="Nada cadastrado"
      loading-label="Carregando..."
      :class="{ 'tabela-clicavel': podeEditar }"
      @row-click="(_, i) => podeEditar && abrir(i)"
    >
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.ativo ? 'positive' : 'grey'">{{ props.row.ativo ? 'Ativo' : 'Inativo' }}</q-badge>
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="dialogo">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="salvar">
          <q-card-section class="piki-titulo">{{ editando.id ? `Editar ${item}` : `${feminino ? 'Nova' : 'Novo'} ${item}` }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-input
              v-model="editando.nome"
              outlined
              autofocus
              label="Nome *"
              :maxlength="tamanho"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            />
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

const props = defineProps({
  titulo: { type: String, required: true },
  item: { type: String, required: true }, // "grupo", "parentesco": vai nos botões
  feminino: { type: Boolean, default: false }, // "Nova marca"
  url: { type: String, required: true },
  permissaoEditar: { type: String, required: true },
  tamanho: { type: Number, default: 40 },
})

const $q = useQuasar()
const sessao = useSessaoStore()
const podeEditar = computed(() => sessao.pode(props.permissaoEditar))

const itens = ref([])
const carregando = ref(false)
const dialogo = ref(false)
const salvando = ref(false)
const editando = ref({})

const colunas = [
  { name: 'nome', label: 'Nome', field: 'nome', align: 'left', sortable: true },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

async function carregar() {
  carregando.value = true
  try {
    itens.value = (await api.get(props.url)).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function abrir(registro) {
  editando.value = registro ? { ...registro } : { nome: '', ativo: true }
  dialogo.value = true
}

async function salvar() {
  salvando.value = true
  try {
    const { id, ...dados } = editando.value
    await (id ? api.put(`${props.url}/${id}`, dados) : api.post(props.url, dados))
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
