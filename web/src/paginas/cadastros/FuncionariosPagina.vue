<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Funcionários</div>
      <q-btn
        v-if="sessao.pode('funcionarios.editar')"
        color="primary"
        unelevated
        no-caps
        icon="add"
        label="Novo funcionário"
        :to="{ name: 'funcionario-novo' }"
      />
    </div>

    <q-table
      flat
      bordered
      :rows="filtrados"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :filter="busca"
      :filter-method="filtrar"
      :pagination="{ rowsPerPage: 20, sortBy: 'nome' }"
      no-data-label="Nenhum funcionário cadastrado"
      no-results-label="Nenhum funcionário encontrado"
      loading-label="Carregando..."
      class="tabela-clicavel"
      @row-click="(_, f) => $router.push({ name: 'funcionario', params: { id: f.id } })"
    >
      <template #top>
        <div class="row items-center q-gutter-md full-width">
          <q-input v-model="busca" dense outlined placeholder="Nome, apelido ou CPF" clearable class="col-12 col-sm">
            <template #prepend><q-icon name="search" /></template>
          </q-input>
          <q-toggle v-model="soDestaLoja" :label="`Só de ${sessao.empresa?.nome}`" />
          <q-toggle v-model="soAtivos" label="Só ativos" />
        </div>
      </template>
      <template #body-cell-nome="props">
        <q-td :props="props">
          <div class="text-weight-medium">{{ props.row.nome }}</div>
          <div v-if="props.row.apelido" class="text-caption text-suave">{{ props.row.apelido }}</div>
        </q-td>
      </template>
      <template #body-cell-empresa="props">
        <q-td :props="props">
          <q-avatar
            text-color="white"
            size="22px"
            font-size="11px"
            class="q-mr-sm"
            :style="{ background: props.row.empresa.tema.principal }"
          >
            {{ props.row.empresa.codigo }}
          </q-avatar>
          {{ props.row.empresa.nome }}
        </q-td>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.ativo ? 'positive' : 'grey'">{{ props.row.ativo ? 'Ativo' : 'Inativo' }}</q-badge>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCpf, soDigitos } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const sessao = useSessaoStore()

const funcionarios = ref([])
const carregando = ref(false)
const busca = ref('')
const soDestaLoja = ref(false)
const soAtivos = ref(true)

const colunas = [
  { name: 'nome', label: 'Nome', field: 'nome', align: 'left', sortable: true },
  { name: 'cpf', label: 'CPF', field: 'cpf', align: 'left', format: (v) => (v ? formatarCpf(v) : '') },
  { name: 'empresa', label: 'Loja', field: (f) => f.empresa.nome, align: 'left', sortable: true },
  { name: 'cargo', label: 'Cargo', field: (f) => f.cargo?.nome ?? '', align: 'left', sortable: true },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

const filtrados = computed(() =>
  funcionarios.value.filter(
    (f) => (!soDestaLoja.value || f.empresa.id === sessao.empresa?.id) && (!soAtivos.value || f.ativo),
  ),
)

function filtrar(linhas, termo) {
  const texto = termo.trim().toLowerCase()
  const digitos = soDigitos(termo)
  return linhas.filter(
    (f) =>
      f.nome.toLowerCase().includes(texto) ||
      (f.apelido ?? '').toLowerCase().includes(texto) ||
      (digitos && (f.cpf ?? '').includes(digitos)),
  )
}

onMounted(async () => {
  carregando.value = true
  try {
    funcionarios.value = (await api.get('/funcionarios')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>
