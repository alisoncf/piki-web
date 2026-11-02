<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Fornecedores</div>
      <q-btn
        v-if="sessao.pode('fornecedores.editar')"
        color="primary"
        unelevated
        no-caps
        icon="add"
        label="Novo fornecedor"
        :to="{ name: 'fornecedor-novo' }"
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
      no-data-label="Nenhum fornecedor cadastrado"
      no-results-label="Nenhum fornecedor encontrado"
      loading-label="Carregando..."
      class="tabela-clicavel"
      @row-click="(_, f) => $router.push({ name: 'fornecedor', params: { id: f.id } })"
    >
      <template #top>
        <div class="row items-center q-gutter-md full-width">
          <q-input v-model="busca" dense outlined placeholder="Razão social, fantasia ou CNPJ" clearable class="col-12 col-sm">
            <template #prepend><q-icon name="search" /></template>
          </q-input>
          <q-toggle v-model="soAtivos" label="Só ativos" />
        </div>
      </template>
      <template #body-cell-nome="props">
        <q-td :props="props">
          <div class="text-weight-medium">{{ props.row.nome }}</div>
          <div v-if="props.row.nome_fantasia" class="text-caption text-suave">{{ props.row.nome_fantasia }}</div>
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
import { formatarDocumento, semAcentos, soDigitos } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const sessao = useSessaoStore()

const fornecedores = ref([])
const carregando = ref(false)
const busca = ref('')
const soAtivos = ref(true)

const colunas = [
  { name: 'nome', label: 'Razão social', field: 'nome', align: 'left', sortable: true },
  { name: 'cpf_cnpj', label: 'CNPJ / CPF', field: 'cpf_cnpj', align: 'left', format: formatarDocumento },
  {
    name: 'cidade', label: 'Cidade', align: 'left', sortable: true,
    field: (f) => (f.cidade ? `${f.cidade.nome} - ${f.cidade.uf}` : ''),
  },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

const filtrados = computed(() => fornecedores.value.filter((f) => !soAtivos.value || f.ativo))

// são poucas centenas: a lista vem inteira e a busca é feita aqui, sem acentos
function filtrar(linhas, termo) {
  const texto = semAcentos(termo.trim().toLowerCase())
  const digitos = soDigitos(termo)
  return linhas.filter(
    (f) =>
      semAcentos(f.nome.toLowerCase()).includes(texto) ||
      semAcentos((f.nome_fantasia ?? '').toLowerCase()).includes(texto) ||
      (digitos && f.cpf_cnpj.startsWith(digitos)),
  )
}

onMounted(async () => {
  carregando.value = true
  try {
    fornecedores.value = (await api.get('/fornecedores')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>
