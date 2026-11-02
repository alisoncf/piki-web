<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Usuários</div>
      <q-btn color="primary" unelevated no-caps icon="person_add" label="Novo usuário" :to="{ name: 'usuario-novo' }" />
    </div>
    <q-table
      flat
      bordered
      :rows="filtrados"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :filter="filtro"
      :pagination="{ rowsPerPage: 20, sortBy: 'nome' }"
      no-data-label="Nenhum usuário cadastrado"
      no-results-label="Nenhum usuário encontrado"
      loading-label="Carregando..."
      class="tabela-clicavel"
      @row-click="(_, u) => $router.push({ name: 'usuario', params: { id: u.id } })"
    >
      <template #top>
        <div class="row items-center q-gutter-md full-width">
          <q-input v-model="filtro" dense outlined placeholder="Nome ou usuário" clearable class="col-12 col-sm">
            <template #prepend><q-icon name="search" /></template>
          </q-input>
          <q-toggle v-model="soDestaEmpresa" :label="`Só de ${sessao.empresa?.nome}`" />
          <q-toggle v-model="soAtivos" label="Só ativos" />
        </div>
      </template>
      <template #body-cell-nome="props">
        <q-td :props="props">
          <div class="text-weight-medium">{{ props.row.nome }}</div>
          <div class="text-caption text-suave">{{ props.row.login }}</div>
        </q-td>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.ativo ? 'positive' : 'grey'">{{ props.row.ativo ? 'Ativo' : 'Inativo' }}</q-badge>
          <q-badge v-if="props.row.administrador" color="accent" text-color="dark" class="q-ml-xs">Administrador</q-badge>
          <q-badge v-if="bloqueado(props.row)" color="negative" class="q-ml-xs">Bloqueado</q-badge>
          <q-badge v-else-if="props.row.trocar_senha" color="warning" text-color="dark" class="q-ml-xs">Senha provisória</q-badge>
        </q-td>
      </template>
      <template #body-cell-acessos="props">
        <q-td :props="props">
          <span v-if="props.row.administrador" class="text-suave">Todas as empresas</span>
          <template v-else>
            <q-chip
              v-for="a in props.row.acessos"
              :key="a.empresa.id"
              dense
              :color="a.ativo ? 'primario-claro' : 'grey-3'"
              :text-color="a.ativo ? 'primary' : 'grey-7'"
            >
              {{ a.empresa.nome }} · {{ a.perfil.nome }}
            </q-chip>
          </template>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const sessao = useSessaoStore()
const usuarios = ref([])
const carregando = ref(false)
const filtro = ref('')
const soAtivos = ref(true)
const soDestaEmpresa = ref(!sessao.usuario?.administrador)

const colunas = [
  { name: 'nome', label: 'Nome', field: (u) => `${u.nome} ${u.login}`, align: 'left', sortable: true, sort: (a, b) => a.localeCompare(b) },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
  { name: 'acessos', label: 'Empresas e perfis', field: (u) => u.acessos.map((a) => a.empresa.nome).join(' '), align: 'left' },
]

function bloqueado(u) {
  return !!u.bloqueado_ate && new Date(u.bloqueado_ate) > new Date()
}

const filtrados = computed(() => usuarios.value.filter((u) =>
  (!soAtivos.value || u.ativo)
  && (!soDestaEmpresa.value || u.administrador || u.acessos.some((a) => a.ativo && a.empresa.id === sessao.empresa?.id))))

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
