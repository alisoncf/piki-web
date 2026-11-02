<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Seções e subseções</div>
      <q-btn v-if="podeEditar" color="primary" unelevated no-caps icon="add" label="Nova seção" @click="abrirSecao()" />
    </div>
    <div class="text-caption text-suave q-mb-md">Todo produto fica numa subseção: Cama › Jogo de cama, Mesa › Toalha de mesa...</div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <div v-else-if="!secoes.length" class="text-suave">Nenhuma seção cadastrada.</div>
    <div v-else class="row q-col-gutter-md">
      <div v-for="s in secoes" :key="s.id" class="col-12 col-md-6 col-lg-4">
        <section class="cartao q-pa-md full-height">
          <div class="row items-center q-mb-sm">
            <div class="formulario__secao col q-mb-none">
              {{ s.nome }} <q-badge v-if="!s.ativo" color="grey">Inativa</q-badge>
            </div>
            <q-btn v-if="podeEditar" flat round dense icon="edit" :aria-label="`Editar a seção ${s.nome}`" @click="abrirSecao(s)" />
          </div>
          <div class="row q-gutter-xs">
            <q-chip
              v-for="sub in s.subsecoes"
              :key="sub.id"
              :clickable="podeEditar"
              :color="sub.ativo ? undefined : 'grey-4'"
              @click="podeEditar && abrirSubsecao(s, sub)"
            >
              {{ sub.nome }}
            </q-chip>
            <q-btn v-if="podeEditar" flat dense no-caps color="primary" icon="add" label="Subseção" @click="abrirSubsecao(s)" />
          </div>
        </section>
      </div>
    </div>

    <q-dialog v-model="dialogo">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="salvar">
          <q-card-section class="piki-titulo">{{ titulo }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-input
              v-model="editando.nome"
              outlined
              autofocus
              label="Nome *"
              :maxlength="editando.tipo === 'secao' ? 40 : 50"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            />
            <q-select
              v-if="editando.tipo === 'subsecao'"
              v-model="editando.secao_id"
              outlined
              label="Seção *"
              :options="secoes"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
            />
            <q-toggle v-model="editando.ativo" label="Ativa" />
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

const $q = useQuasar()
const sessao = useSessaoStore()
const podeEditar = computed(() => sessao.pode('produtos.editar'))

const secoes = ref([])
const carregando = ref(true)
const dialogo = ref(false)
const salvando = ref(false)
const editando = ref({})

const titulo = computed(() => {
  const { tipo, id } = editando.value
  if (tipo === 'secao') return id ? 'Editar seção' : 'Nova seção'
  return id ? 'Editar subseção' : 'Nova subseção'
})

async function carregar() {
  try {
    secoes.value = (await api.get('/secoes')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function abrirSecao(secao) {
  editando.value = { tipo: 'secao', id: secao?.id, nome: secao?.nome ?? '', ativo: secao?.ativo ?? true }
  dialogo.value = true
}

function abrirSubsecao(secao, sub) {
  editando.value = { tipo: 'subsecao', id: sub?.id, nome: sub?.nome ?? '', ativo: sub?.ativo ?? true, secao_id: secao.id }
  dialogo.value = true
}

async function salvar() {
  salvando.value = true
  try {
    const { tipo, id, ...dados } = editando.value
    const url = tipo === 'secao' ? '/secoes' : '/subsecoes'
    await (id ? api.put(`${url}/${id}`, dados) : api.post(url, dados))
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
