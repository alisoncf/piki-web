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
          <q-toggle v-model="semCobrador" :label="`Sem cobrador em ${sessao.empresa?.nome}`" />
        </div>
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
            <q-input v-model="editando.cidade" outlined label="Cidade" maxlength="40" class="col-9" />
            <q-input v-model="editando.uf" outlined label="UF" mask="AA" class="col-3" @update:model-value="(v) => (editando.uf = v?.toUpperCase())" />

            <div class="col-12 formulario__secao q-mt-sm">Cobrador em cada loja</div>
            <q-select
              v-for="loja in sessao.empresas"
              :key="loja.id"
              v-model="editando.cobradores[loja.id]"
              outlined
              :label="loja.nome"
              :options="cobradoresPossiveis(editando.cobradores[loja.id])"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              clearable
              class="col-12 col-sm-6"
            >
              <template #prepend>
                <q-avatar text-color="white" size="22px" font-size="11px" :style="{ background: loja.cor }">{{ loja.codigo }}</q-avatar>
              </template>
            </q-select>
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
const semCobrador = ref(false)
const dialogo = ref(false)
const salvando = ref(false)
// cobradores: { empresa_id: funcionario_id }; os de lojas que o usuário não vê ficam guardados à parte
const editando = ref({ cobradores: {} })
const outrasLojas = ref([])

function cobradorAqui(setor) {
  return setor.cobradores.find((c) => c.empresa.id === sessao.empresa?.id)?.funcionario.nome ?? ''
}

const colunas = [
  { name: 'nome', label: 'Nome', field: 'nome', align: 'left', sortable: true },
  { name: 'tipo', label: 'Tipo', field: 'tipo', align: 'left', sortable: true },
  { name: 'cidade', label: 'Cidade', field: 'cidade', align: 'left', sortable: true },
  { name: 'cobrador', label: 'Cobrador nesta loja', field: cobradorAqui, align: 'left', sortable: true },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

const setores = computed(() => (semCobrador.value ? todos.value.filter((s) => !cobradorAqui(s)) : todos.value))

function filtrar(linhas, termo) {
  const t = semAcentos(termo.trim())
  return linhas.filter((s) => semAcentos(s.nome).includes(t) || semAcentos(s.cidade).includes(t))
}

// quem cobra (cargo marcado como "cobra"); sem nenhum marcado, todos os ativos. O atual fica na lista.
function cobradoresPossiveis(atual) {
  const ativos = funcionarios.value.filter((f) => f.ativo)
  const cobram = ativos.filter((f) => f.cargo?.cobra)
  const lista = cobram.length ? cobram : ativos
  const escolhido = funcionarios.value.find((f) => f.id === atual)
  return escolhido && !lista.includes(escolhido) ? [escolhido, ...lista] : lista
}

async function carregar() {
  carregando.value = true
  try {
    // a lista de funcionários só serve para escolher o cobrador, e exige outra permissão
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
  const visiveis = new Set(sessao.empresas.map((e) => e.id))
  const cobradores = {}
  outrasLojas.value = []
  for (const c of setor?.cobradores ?? []) {
    if (visiveis.has(c.empresa.id)) cobradores[c.empresa.id] = c.funcionario.id
    else outrasLojas.value.push({ empresa_id: c.empresa.id, funcionario_id: c.funcionario.id })
  }
  editando.value = setor
    ? { id: setor.id, nome: setor.nome, tipo: setor.tipo, cidade: setor.cidade, uf: setor.uf, ativo: setor.ativo, cobradores }
    : { nome: '', tipo: '', cidade: '', uf: '', ativo: true, cobradores }
  dialogo.value = true
}

async function salvar() {
  salvando.value = true
  try {
    const { id, cobradores, ...dados } = editando.value
    const lista = Object.entries(cobradores)
      .filter(([, funcionario]) => funcionario)
      .map(([empresa, funcionario]) => ({ empresa_id: Number(empresa), funcionario_id: funcionario }))
    const corpo = { ...dados, cobradores: [...lista, ...outrasLojas.value] }
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
