<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'perfis' }" />
      <div class="piki-titulo col">{{ novo ? 'Novo perfil' : form.nome || 'Perfil' }}</div>
    </div>
    <div v-if="!novo && usuarios" class="text-caption text-suave q-mb-md">
      Usado em {{ usuarios }} {{ usuarios === 1 ? 'acesso' : 'acessos' }}: a mudança vale para todos, em todas as empresas.
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>

    <q-form v-else class="formulario" @submit.prevent="salvar">
      <section class="cartao q-pa-md q-mb-md">
        <div class="row q-col-gutter-md">
          <q-input
            v-model="form.nome"
            outlined
            label="Nome *"
            maxlength="50"
            :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            class="col-12 col-md-4"
          />
          <q-input v-model="form.descricao" outlined label="Descrição" maxlength="150" class="col-12 col-md-8" />
        </div>
      </section>

      <section v-for="area in areas" :key="area.nome" class="cartao q-pa-md q-mb-md">
        <div class="row items-center q-mb-sm">
          <div class="formulario__secao col q-mb-none">{{ area.nome }}</div>
          <q-btn
            flat
            dense
            no-caps
            color="primary"
            :label="area.permissoes.every((p) => marcadas.has(p.codigo)) ? 'Desmarcar todas' : 'Marcar todas'"
            @click="alternarArea(area)"
          />
        </div>
        <div v-for="p in area.permissoes" :key="p.codigo">
          <q-checkbox
            :model-value="marcadas.has(p.codigo)"
            :label="p.descricao"
            :disable="!podeMarcar(p.codigo)"
            @update:model-value="(v) => marcar(p.codigo, v)"
          >
            <q-tooltip v-if="!podeMarcar(p.codigo)">Você não tem esta permissão para dar</q-tooltip>
          </q-checkbox>
        </div>
      </section>

      <div class="formulario__acoes row q-gutter-sm q-mb-md">
        <q-btn v-if="!novo" flat no-caps color="negative" icon="delete" label="Excluir" :disable="usuarios > 0" @click="excluir">
          <q-tooltip v-if="usuarios > 0">Há usuários com este perfil</q-tooltip>
        </q-btn>
        <q-space />
        <q-btn flat no-caps label="Cancelar" :to="{ name: 'perfis' }" />
        <q-btn type="submit" color="primary" unelevated no-caps icon="check" label="Salvar" :loading="salvando" />
      </div>
    </q-form>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()

const novo = computed(() => !rota.params.id)
const carregando = ref(true)
const salvando = ref(false)
const catalogo = ref([])
const form = ref({ nome: '', descricao: '' })
const marcadas = ref(new Set())
const originais = ref(new Set()) // as que o perfil já tinha: tirar sempre pode
const usuarios = ref(0)

// as permissões agrupadas por área, na ordem do catálogo
const areas = computed(() => {
  const grupos = []
  for (const p of catalogo.value) {
    let grupo = grupos.find((g) => g.nome === p.area)
    if (!grupo) grupos.push((grupo = { nome: p.area, permissoes: [] }))
    grupo.permissoes.push(p)
  }
  return grupos
})

// quem não é administrador só dá o que tem (a API confere de novo)
function podeMarcar(codigo) {
  return sessao.usuario?.administrador || sessao.pode(codigo) || originais.value.has(codigo)
}

function marcar(codigo, sim) {
  const novas = new Set(marcadas.value)
  if (sim) novas.add(codigo)
  else novas.delete(codigo)
  marcadas.value = novas
}

function alternarArea(area) {
  const todas = area.permissoes.every((p) => marcadas.value.has(p.codigo))
  for (const p of area.permissoes) if (todas || podeMarcar(p.codigo)) marcar(p.codigo, !todas)
}

function preencher(perfil) {
  form.value = { nome: perfil.nome, descricao: perfil.descricao ?? '' }
  marcadas.value = new Set(perfil.permissoes)
  originais.value = new Set(perfil.permissoes)
  usuarios.value = perfil.usuarios
}

onMounted(async () => {
  try {
    const [lista, perfil] = await Promise.all([
      api.get('/acesso/permissoes'),
      novo.value ? null : api.get(`/acesso/perfis/${rota.params.id}`),
    ])
    catalogo.value = lista.data
    if (perfil) preencher(perfil.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

async function salvar() {
  salvando.value = true
  try {
    const dados = { ...form.value, permissoes: [...marcadas.value] }
    const resp = novo.value ? await api.post('/acesso/perfis', dados) : await api.put(`/acesso/perfis/${rota.params.id}`, dados)
    $q.notify({ type: 'positive', message: 'Perfil salvo', timeout: 1500 })
    if (novo.value) await roteador.replace({ name: 'perfil', params: { id: resp.data.id } })
    preencher(resp.data)
    // se for o perfil de quem está na tela, as permissões dele mudam na hora
    await sessao.carregarEu()
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

function excluir() {
  $q.dialog({
    title: 'Excluir perfil',
    message: `Excluir o perfil ${form.value.nome}?`,
    cancel: { flat: true, label: 'Não' },
    ok: { label: 'Excluir', color: 'negative' },
  }).onOk(async () => {
    try {
      await api.delete(`/acesso/perfis/${rota.params.id}`)
      await roteador.push({ name: 'perfis' })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}
</script>
