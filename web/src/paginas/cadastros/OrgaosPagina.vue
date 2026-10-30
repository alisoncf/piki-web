<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Órgãos</div>
      <q-btn v-if="podeEditar" color="primary" unelevated no-caps icon="add" label="Novo órgão" @click="abrir()" />
    </div>

    <q-table
      flat
      bordered
      :rows="orgaos"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :filter="busca"
      :filter-method="filtrar"
      :pagination="{ rowsPerPage: 20, sortBy: 'nome' }"
      :rows-per-page-options="[20, 50, 100]"
      rows-per-page-label="Por página"
      no-data-label="Nenhum órgão cadastrado"
      no-results-label="Nenhum órgão encontrado"
      loading-label="Carregando..."
      :class="{ 'tabela-clicavel': podeEditar }"
      @row-click="(_, o) => podeEditar && abrir(o)"
    >
      <template #top>
        <q-input v-model="busca" dense outlined placeholder="Nome do órgão" clearable class="full-width">
          <template #prepend><q-icon name="search" /></template>
        </q-input>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge :color="props.row.ativo ? 'positive' : 'grey'">{{ props.row.ativo ? 'Ativo' : 'Inativo' }}</q-badge>
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="dialogo">
      <q-card class="cartao-medio">
        <q-form @submit.prevent="salvar">
          <q-card-section class="piki-titulo">{{ editando.id ? 'Editar órgão' : 'Novo órgão' }}</q-card-section>
          <q-card-section class="row q-col-gutter-md q-pt-none">
            <q-input
              v-model="editando.nome"
              outlined
              autofocus
              label="Nome *"
              maxlength="60"
              class="col-12"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            />
            <q-select
              v-model="editando.grupo_id"
              outlined
              label="Grupo"
              :options="grupos"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              clearable
              class="col-12 col-sm-6"
            />
            <selecao-busca v-model="editando.setor_id" :opcoes="setores" :rotulo="nomeSetor" label="Setor" class="col-12 col-sm-6" />
            <q-input v-model="editando.endereco" outlined label="Endereço" maxlength="60" class="col-12" />
            <q-input v-model="editando.cep" outlined label="CEP" mask="#####-###" unmasked-value class="col-6" />
            <q-input
              v-model="editando.telefone"
              outlined
              label="Telefone"
              :mask="mascaraTelefone(editando.telefone)"
              unmasked-value
              class="col-6"
            />
            <q-input v-model="editando.observacao" outlined label="Observações" type="textarea" autogrow maxlength="2000" class="col-12" />
            <q-toggle v-model="editando.ativo" label="Ativo" class="col-12" />
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

import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { formatarTelefone, mascaraTelefone, semAcentos } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const sessao = useSessaoStore()
const podeEditar = computed(() => sessao.pode('clientes.editar'))

const orgaos = ref([])
const grupos = ref([])
const setores = ref([])
const carregando = ref(false)
const busca = ref('')
const dialogo = ref(false)
const salvando = ref(false)
const editando = ref({})

const colunas = [
  { name: 'nome', label: 'Nome', field: 'nome', align: 'left', sortable: true },
  { name: 'grupo', label: 'Grupo', field: (o) => o.grupo?.nome ?? '', align: 'left', sortable: true },
  { name: 'setor', label: 'Setor', field: (o) => o.setor?.nome ?? '', align: 'left', sortable: true },
  { name: 'telefone', label: 'Telefone', field: 'telefone', align: 'left', format: (v) => (v ? formatarTelefone(v) : '') },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

function nomeSetor(s) {
  return s ? (s.cidade ? `${s.nome} (${s.cidade})` : s.nome) : ''
}

function filtrar(linhas, termo) {
  const t = semAcentos(termo.trim())
  return linhas.filter((o) => semAcentos(o.nome).includes(t))
}

async function carregar() {
  carregando.value = true
  try {
    const [o, g, s] = await Promise.all(['/orgaos', '/grupos-clientes', '/setores'].map((url) => api.get(url)))
    orgaos.value = o.data
    grupos.value = g.data
    setores.value = s.data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function abrir(orgao) {
  if (orgao) {
    const { id, nome, grupo_id, setor_id, endereco, cep, telefone, observacao, ativo } = orgao
    editando.value = { id, nome, grupo_id, setor_id, endereco, cep, telefone, observacao, ativo }
  } else {
    editando.value = { nome: '', grupo_id: null, setor_id: null, endereco: '', cep: '', telefone: '', observacao: '', ativo: true }
  }
  dialogo.value = true
}

async function salvar() {
  salvando.value = true
  try {
    const { id, ...dados } = editando.value
    await (id ? api.put(`/orgaos/${id}`, dados) : api.post('/orgaos', dados))
    dialogo.value = false
    orgaos.value = (await api.get('/orgaos')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

onMounted(carregar)
</script>
