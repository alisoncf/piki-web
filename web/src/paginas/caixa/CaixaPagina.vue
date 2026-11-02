<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Caixa</div>
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <div v-else-if="!ativos.length" class="text-suave">Nenhum caixa cadastrado nesta loja.</div>
    <div v-else class="row q-col-gutter-md">
      <div v-for="c in ativos" :key="c.id" class="col-12 col-sm-6 col-md-4">
        <section class="cartao q-pa-md full-height column">
          <div class="row items-center q-mb-sm">
            <div class="text-h6 col">{{ c.nome }}</div>
            <q-badge v-if="caixaDaMaquina.caixa?.id === c.id" color="primary" class="q-mr-xs">Este computador</q-badge>
            <q-badge :color="c.sessao ? 'positive' : 'grey'">{{ c.sessao ? 'Aberto' : 'Fechado' }}</q-badge>
          </div>
          <div class="text-caption text-suave col">
            <template v-if="c.sessao">Aberto por {{ c.sessao.aberto_por.nome }} em {{ formatarDataHora(c.sessao.aberto_em) }}</template>
            <template v-else>Fechado</template>
          </div>
          <div class="row q-gutter-sm q-mt-md">
            <q-btn v-if="c.sessao" unelevated no-caps color="primary" icon="point_of_sale" label="Entrar" @click="entrar(c, c.sessao.id)">
              <q-tooltip>Este computador passa a receber as vendas no {{ c.nome }}</q-tooltip>
            </q-btn>
            <q-btn v-else-if="sessao.pode('caixa.operar')" unelevated no-caps color="primary" icon="lock_open" label="Abrir" @click="pedirAbertura(c)" />
            <q-btn v-if="sessao.pode('caixa.conferir')" flat no-caps color="primary" icon="history" label="Fechamentos" @click="verFechamentos(c)" />
          </div>
        </section>
      </div>
    </div>

    <q-dialog v-model="abrindo">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="abrir">
          <q-card-section class="piki-titulo">Abrir {{ escolhido?.nome }}</q-card-section>
          <q-card-section class="q-pt-none">
            <q-input v-model="fundo" outlined autofocus type="number" step="0.01" min="0" prefix="R$" label="Fundo de troco" hint="O dinheiro que já está na gaveta" />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Abrir" :loading="salvando" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="vendoFechamentos">
      <q-card style="width: 640px; max-width: 95vw">
        <q-card-section class="piki-titulo">Fechamentos · {{ escolhido?.nome }}</q-card-section>
        <q-card-section class="q-pt-none">
          <q-table
            flat
            dense
            :rows="fechamentos"
            :columns="colunasFechamentos"
            row-key="id"
            :loading="carregandoFechamentos"
            :pagination="{ rowsPerPage: 10 }"
            no-data-label="Nenhum fechamento"
            class="tabela-clicavel"
            @row-click="(_, s) => $router.push({ name: 'sessao-caixa', params: { id: s.id } })"
          />
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora } from '@/servicos/formatos'
import { useCaixaDaMaquinaStore } from '@/stores/caixaDaMaquina'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const roteador = useRouter()
const sessao = useSessaoStore()

const caixas = ref([])
const carregando = ref(true)
const salvando = ref(false)
const abrindo = ref(false)
const escolhido = ref(null)
const fundo = ref('')
const vendoFechamentos = ref(false)
const fechamentos = ref([])
const carregandoFechamentos = ref(false)

const ativos = computed(() => caixas.value.filter((c) => c.ativo || c.sessao))
const colunasFechamentos = [
  { name: 'aberto', label: 'Aberto', field: 'aberto_em', align: 'left', format: formatarDataHora },
  { name: 'fechado', label: 'Fechado', field: 'fechado_em', align: 'left', format: (v) => (v ? formatarDataHora(v) : 'Aberto') },
  { name: 'quem', label: 'Quem fechou', field: (s) => s.fechado_por?.nome ?? '', align: 'left' },
]

onMounted(async () => {
  try {
    caixas.value = (await api.get('/caixas')).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

const caixaDaMaquina = useCaixaDaMaquinaStore()

function entrar(caixa, sessaoId) {
  caixaDaMaquina.entrar(caixa)
  roteador.push({ name: 'sessao-caixa', params: { id: sessaoId } })
}

function pedirAbertura(caixa) {
  escolhido.value = caixa
  fundo.value = ''
  abrindo.value = true
}

async function abrir() {
  salvando.value = true
  try {
    const { data } = await api.post(`/caixas/${escolhido.value.id}/abrir`, { fundo: fundo.value === '' ? '0' : String(fundo.value) })
    abrindo.value = false
    entrar(escolhido.value, data.id)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

async function verFechamentos(caixa) {
  escolhido.value = caixa
  vendoFechamentos.value = true
  carregandoFechamentos.value = true
  try {
    fechamentos.value = (await api.get(`/caixas/${caixa.id}/sessoes`, { params: { limite: 50 } })).data.itens
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregandoFechamentos.value = false
  }
}
</script>
