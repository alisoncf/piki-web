<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Setores</div>
      <q-btn v-if="podeEditar" color="primary" unelevated no-caps icon="add" label="Novo setor" @click="abrir()" />
    </div>

    <q-table
      flat
      bordered
      :rows="setores"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :filter="busca"
      :filter-method="filtrar"
      :pagination="{ rowsPerPage: 20, sortBy: 'nome' }"
      :rows-per-page-options="[20, 50, 100]"
      rows-per-page-label="Por página"
      no-data-label="Nenhum setor cadastrado"
      no-results-label="Nenhum setor encontrado"
      loading-label="Carregando..."
      :class="{ 'tabela-clicavel': podeEditar }"
      @row-click="(_, s) => podeEditar && abrir(s)"
    >
      <template #top>
        <div class="row items-center q-gutter-md full-width">
          <q-input v-model="busca" dense outlined placeholder="Nome do setor ou cidade" clearable class="col-12 col-sm">
            <template #prepend><q-icon name="search" /></template>
          </q-input>
          <q-select
            v-model="filtroCobrador"
            dense
            outlined
            clearable
            label="Cobrador"
            :options="cobradoresNosSetores"
            option-value="id"
            option-label="nome"
            emit-value
            map-options
            class="col-12 col-sm-3"
          />
          <q-toggle v-model="semCobrador" label="Sem cobrador" />
        </div>
      </template>
      <template #body-cell-cobradores="props">
        <q-td :props="props">
          <q-chip v-for="c in props.row.cobradores" :key="c.id" dense square>{{ c.nome }}</q-chip>
        </q-td>
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
          <q-card-section class="piki-titulo">{{ editando.id ? 'Editar setor' : 'Novo setor' }}</q-card-section>
          <q-card-section class="row q-col-gutter-md q-pt-none">
            <q-input
              v-model="editando.nome"
              outlined
              autofocus
              label="Nome *"
              maxlength="40"
              class="col-12 col-sm-8"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            />
            <q-input v-model="editando.tipo" outlined label="Tipo" hint="Bairro, vila, jardim..." maxlength="20" class="col-12 col-sm-4" />
            <selecao-cidade
              v-model="editando.cidade_id"
              v-model:cidade="editando.cidade"
              label="Cidade *"
              class="col-12"
              :rules="[(v) => !!v || 'Escolha a cidade']"
            />
            <q-select
              v-model="editando.cobradores"
              outlined
              multiple
              use-chips
              label="Cobradores"
              hint="Funcionários; valem para todas as lojas"
              :options="cobradoresPossiveis(editando.cobradores)"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              class="col-12"
            />
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

import SelecaoCidade from '@/componentes/SelecaoCidade.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { semAcentos } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const sessao = useSessaoStore()
const podeEditar = computed(() => sessao.pode('clientes.editar'))

const todos = ref([])
const funcionarios = ref([])
const carregando = ref(false)
const busca = ref('')
const filtroCobrador = ref(null)
const semCobrador = ref(false)
const dialogo = ref(false)
const salvando = ref(false)
const editando = ref({ cobradores: [] })

function nomeCidade(setor) {
  return setor.cidade ? `${setor.cidade.nome} - ${setor.cidade.uf}` : ''
}

const colunas = [
  { name: 'nome', label: 'Nome', field: 'nome', align: 'left', sortable: true },
  { name: 'tipo', label: 'Tipo', field: 'tipo', align: 'left', sortable: true },
  { name: 'cidade', label: 'Cidade', field: nomeCidade, align: 'left', sortable: true },
  { name: 'cobradores', label: 'Cobradores', field: 'cobradores', align: 'left' },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

const setores = computed(() =>
  todos.value.filter(
    (s) =>
      (!semCobrador.value || !s.cobradores.length) &&
      (!filtroCobrador.value || s.cobradores.some((c) => c.id === filtroCobrador.value)),
  ),
)

function filtrar(linhas, termo) {
  const t = semAcentos(termo.trim())
  return linhas.filter((s) => semAcentos(s.nome).includes(t) || semAcentos(nomeCidade(s)).includes(t))
}

// quem aparece em algum setor, para o filtro (não depende de poder ver funcionários)
const cobradoresNosSetores = computed(() => {
  const unicos = new Map(todos.value.flatMap((s) => s.cobradores).map((c) => [c.id, c]))
  return [...unicos.values()].sort((a, b) => a.nome.localeCompare(b.nome))
})

// funcionários ativos de cargo que cobra (ou todos os ativos, se nenhum cargo cobra);
// os que já estão no setor continuam na lista
function cobradoresPossiveis(escolhidos) {
  const ativos = funcionarios.value.filter((f) => f.ativo)
  const cobram = ativos.filter((f) => f.cargo?.cobra)
  const lista = cobram.length ? cobram : ativos
  const doSetor = cobradoresNosSetores.value.filter((c) => escolhidos.includes(c.id) && !lista.some((f) => f.id === c.id))
  return [...doSetor, ...lista]
}

async function carregar() {
  carregando.value = true
  try {
    // a lista de funcionários só serve para escolher cobradores, e exige outra permissão
    const [s, f] = await Promise.all([
      api.get('/setores'),
      sessao.pode('funcionarios.ver') ? api.get('/funcionarios') : { data: [] },
    ])
    todos.value = s.data
    funcionarios.value = f.data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function abrir(setor) {
  editando.value = setor
    ? {
        id: setor.id,
        nome: setor.nome,
        tipo: setor.tipo,
        cidade_id: setor.cidade_id,
        cidade: setor.cidade,
        ativo: setor.ativo,
        cobradores: setor.cobradores.map((c) => c.id),
      }
    : { nome: '', tipo: '', cidade_id: null, cidade: null, ativo: true, cobradores: [] }
  dialogo.value = true
}

async function salvar() {
  salvando.value = true
  try {
    // a cidade inteira só serve para o campo mostrar o nome; vai só o id
    const { id, nome, tipo, cidade_id, ativo, cobradores } = editando.value
    const corpo = { nome, tipo, cidade_id, ativo, cobradores }
    await (id ? api.put(`/setores/${id}`, corpo) : api.post('/setores', corpo))
    dialogo.value = false
    todos.value = (await api.get('/setores')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

onMounted(carregar)
</script>
