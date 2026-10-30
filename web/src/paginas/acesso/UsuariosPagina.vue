<template>
  <q-page padding>
    <div class="text-h5 q-mb-md">Usuários</div>
    <q-table
      flat
      bordered
      :rows="usuarios"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :filter="filtro"
      :pagination="{ rowsPerPage: 20 }"
      no-data-label="Nenhum usuário cadastrado"
      no-results-label="Nenhum usuário encontrado"
      loading-label="Carregando..."
    >
      <template #top-right>
        <q-input v-model="filtro" dense outlined placeholder="Buscar" clearable>
          <template #prepend><q-icon name="search" /></template>
        </q-input>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.ativo ? 'positive' : 'grey'">{{ props.row.ativo ? 'Ativo' : 'Inativo' }}</q-badge>
          <q-badge v-if="props.row.administrador" color="accent" class="q-ml-xs">Administrador</q-badge>
        </q-td>
      </template>
      <template #body-cell-acessos="props">
        <q-td :props="props">
          <span v-if="props.row.administrador" class="text-grey-7">Todas as empresas</span>
          <template v-else>
            <q-chip
              v-for="a in props.row.acessos"
              :key="a.empresa.id"
              dense
              :color="a.ativo ? 'blue-1' : 'grey-3'"
              :text-color="a.ativo ? 'primary' : 'grey-7'"
            >
              {{ a.empresa.nome }} · {{ a.perfil }}
            </q-chip>
          </template>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'

const $q = useQuasar()
const usuarios = ref([])
const carregando = ref(false)
const filtro = ref('')

const colunas = [
  { name: 'nome', label: 'Nome', field: 'nome', align: 'left', sortable: true },
  { name: 'login', label: 'Usuário', field: 'login', align: 'left', sortable: true },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
  { name: 'acessos', label: 'Empresas e perfis', field: (u) => u.acessos.map((a) => a.empresa.nome).join(' '), align: 'left' },
]

onMounted(async () => {
  carregando.value = true
  try {
    usuarios.value = (await api.get('/acesso/usuarios')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>
