<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Perfis</div>
      <q-btn color="primary" unelevated no-caps icon="add" label="Novo perfil" :to="{ name: 'perfil-novo' }" />
    </div>
    <div class="text-caption text-suave q-mb-md">
      O perfil é o conjunto do que a pessoa pode fazer (Caixa, Vendedor, Gerente...). Cada usuário tem um perfil em cada empresa.
    </div>
    <q-table
      flat
      bordered
      :rows="perfis"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 0 }"
      hide-pagination
      no-data-label="Nenhum perfil cadastrado"
      loading-label="Carregando..."
      class="tabela-clicavel"
      @row-click="(_, p) => $router.push({ name: 'perfil', params: { id: p.id } })"
    >
      <template #body-cell-nome="props">
        <q-td :props="props">
          <div class="text-weight-medium">{{ props.row.nome }}</div>
          <div v-if="props.row.descricao" class="text-caption text-suave">{{ props.row.descricao }}</div>
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
const perfis = ref([])
const carregando = ref(false)

const colunas = [
  { name: 'nome', label: 'Perfil', field: 'nome', align: 'left', sortable: true },
  { name: 'permissoes', label: 'Permissões', field: (p) => p.permissoes.length, align: 'right', sortable: true },
  { name: 'usuarios', label: 'Usuários', field: 'usuarios', align: 'right', sortable: true },
]

onMounted(async () => {
  carregando.value = true
  try {
    perfis.value = (await api.get('/acesso/perfis')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>
