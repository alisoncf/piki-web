<template>
  <!-- o balcão do consignado (D30): o representante escolhe os produtos e confirma com a senha dele -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">{{ transferencia ? `Transferência ${transferencia.numero}` : 'Transferência ao representante' }}</div>
      <q-btn flat no-caps icon="list" label="Transferências" :to="{ name: 'transferencias' }" />
    </div>

    <section v-if="!transferencia" class="cartao q-pa-md">
      <q-select
        v-model="representanteId"
        outlined
        use-input
        autofocus
        input-debounce="300"
        label="Representante (nome, CPF ou código)"
        :options="representantes"
        option-value="id"
        :option-label="(r) => (r?.cliente ? `${r.codigo} · ${r.cliente.nome}` : '')"
        emit-value
        map-options
        @filter="buscarRepresentantes"
        @update:model-value="abrir"
      >
        <template #option="{ itemProps, opt }">
          <q-item v-bind="itemProps">
            <q-item-section>
              <q-item-label>{{ opt.codigo }} · {{ opt.cliente.nome }}</q-item-label>
              <q-item-label caption>Limite {{ formatarMoeda(opt.limite) }}</q-item-label>
            </q-item-section>
            <q-item-section v-if="opt.bloqueado" side><q-badge color="negative">Bloqueado</q-badge></q-item-section>
          </q-item>
        </template>
        <template #no-option><q-item><q-item-section class="text-suave">Digite ao menos duas letras ou o código</q-item-section></q-item></template>
      </q-select>
    </section>

    <div v-else class="row q-col-gutter-md">
      <div class="col-12 col-md-8">
        <q-banner v-if="transferencia.representante.lembrete" rounded class="bg-amber-1 q-mb-md">
          <q-icon name="push_pin" class="q-mr-sm" />{{ transferencia.representante.lembrete }}
        </q-banner>
        <section class="cartao q-pa-md q-mb-md">
          <form class="row q-col-gutter-sm items-start" @submit.prevent="procurar">
            <q-input ref="campoBusca" v-model="termo" outlined autofocus label="Código, código de barras ou nome do produto" :loading="procurando" class="col">
              <template #prepend><q-icon name="qr_code_scanner" /></template>
            </q-input>
            <q-input v-model="quantidade" outlined type="number" step="any" min="0" label="Qtd." class="col-3 col-sm-2" />
            <div class="col-auto"><q-btn type="submit" unelevated no-caps color="primary" icon="add" label="Incluir" class="q-py-sm" /></div>
          </form>
          <q-list v-if="resultados.length" bordered separator class="q-mt-sm rounded-borders">
            <q-item v-for="p in resultados" :key="p.id" v-ripple clickable @click="incluir(p)">
              <q-item-section>
                <q-item-label>{{ p.nome }}</q-item-label>
                <q-item-label caption>{{ formatarCodigoProduto(p.codigo) }}<template v-if="p.estoque !== null && p.estoque !== undefined"> · estoque {{ formatarQuantidade(p.estoque) }}</template></q-item-label>
              </q-item-section>
              <q-item-section side>{{ formatarMoeda(p.preco_venda) }}</q-item-section>
            </q-item>
          </q-list>
        </section>

        <q-table flat bordered :rows="transferencia.itens" :columns="colunas" row-key="id" :pagination="{ rowsPerPage: 0 }" hide-pagination no-data-label="Nenhum produto ainda">
          <template #body-cell-quantidade="props">
            <q-td :props="props">
              <q-input
                :model-value="props.row.quantidade"
                dense
                outlined
                type="number"
                step="any"
                min="0"
                class="campo-quantidade"
                @change="(v) => alterar(props.row, v)"
              />
            </q-td>
          </template>
          <template #body-cell-acoes="props">
            <q-td :props="props"><q-btn flat round dense icon="delete_outline" aria-label="Tirar" @click="alterar(props.row, 0)" /></q-td>
          </template>
        </q-table>
      </div>

      <div class="col-12 col-md-4">
        <section class="cartao q-pa-md q-mb-md">
          <div class="text-weight-medium">{{ transferencia.representante.codigo }} · {{ transferencia.representante.cliente.nome }}</div>
          <q-badge v-if="transferencia.representante.bloqueado" color="negative" class="q-mt-xs">Bloqueado: não leva mercadoria</q-badge>
          <q-list v-if="posicao" dense class="q-mt-sm">
            <q-item><q-item-section>Limite</q-item-section><q-item-section side>{{ formatarMoeda(posicao.limite) }}</q-item-section></q-item>
            <q-item><q-item-section>Em uso (preço da transferência)</q-item-section><q-item-section side>{{ formatarMoeda(posicao.em_uso) }}</q-item-section></q-item>
            <q-item><q-item-section class="text-suave">Em uso (preço atual)</q-item-section><q-item-section side class="text-suave">{{ formatarMoeda(posicao.em_uso_atual) }}</q-item-section></q-item>
            <q-item><q-item-section>Esta transferência</q-item-section><q-item-section side class="text-weight-bold">{{ formatarMoeda(transferencia.total) }}</q-item-section></q-item>
            <q-item>
              <q-item-section>Resta do limite</q-item-section>
              <q-item-section side :class="resta < 0 ? 'text-negative text-weight-bold' : 'text-positive'">{{ formatarMoeda(resta) }}</q-item-section>
            </q-item>
          </q-list>
          <div v-if="resta < 0" class="text-negative text-caption q-mt-xs">Passa do limite: assim não leva.</div>
        </section>
        <div class="column q-gutter-sm">
          <q-btn unelevated no-caps color="primary" icon="draw" label="Confirmar com a senha do representante" :disable="!transferencia.itens.length" @click="confirmar" />
          <q-btn flat no-caps color="grey-8" icon="delete_outline" label="Descartar" @click="descartar" />
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCodigoProduto, formatarMoeda, formatarQuantidade } from '@/servicos/formatos'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const representantes = ref([])
const representanteId = ref(null)
const transferencia = ref(null)
const posicao = ref(null)
const termo = ref('')
const quantidade = ref('1')
const procurando = ref(false)
const resultados = ref([])
const campoBusca = ref(null)

const resta = computed(() => (posicao.value ? Number(posicao.value.disponivel) - Number(transferencia.value.total) : 0))

const colunas = [
  { name: 'descricao', label: 'Produto', field: (i) => `${formatarCodigoProduto(i.produto.codigo)} · ${i.descricao}`, align: 'left' },
  { name: 'quantidade', label: 'Qtd.', field: 'quantidade', align: 'left' },
  { name: 'preco', label: 'Preço', field: 'preco', format: formatarMoeda, align: 'right' },
  { name: 'total', label: 'Total', field: 'total', format: formatarMoeda, align: 'right' },
  { name: 'acoes', label: '', field: 'id' },
]

function buscarRepresentantes(texto, atualizar, cancelar) {
  if (texto.trim().length < 2 && !/^\d+$/.test(texto.trim())) return cancelar()
  api
    .get('/representantes', { params: { busca: texto.trim(), so_ativos: true } })
    .then(({ data }) => atualizar(() => (representantes.value = data)))
    .catch(() => cancelar())
}

async function mostrar(dados) {
  transferencia.value = dados
  if (rota.params.id !== String(dados.id)) roteador.replace({ name: 'transferencia', params: { id: dados.id } })
  posicao.value = (await api.get(`/representantes/${dados.representante.id}/posicao`)).data
}

async function acao(fazer) {
  try {
    const { data } = await fazer()
    transferencia.value = data
    return data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e), timeout: 8000 })
    return null
  }
}

async function abrir(id) {
  if (!id) return
  try {
    await mostrar((await api.post('/consignacao/transferencias', { representante_id: id })).data)
  } catch (e) {
    representanteId.value = null
    $q.notify({ type: 'negative', message: mensagemDeErro(e), timeout: 8000 })
  }
}

async function procurar() {
  const texto = termo.value.trim()
  if (!texto) return
  procurando.value = true
  try {
    const { data } = await api.get('/produtos', { params: { busca: texto, limite: 20 } })
    if (data.itens.length === 1) await incluir(data.itens[0])
    else if (!data.itens.length) $q.notify({ type: 'warning', message: 'Nenhum produto encontrado' })
    else resultados.value = data.itens
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    procurando.value = false
  }
}

async function incluir(produto) {
  const url = `/consignacao/transferencias/${transferencia.value.id}/itens`
  if (await acao(() => api.post(url, { produto_id: produto.id, quantidade: String(quantidade.value || 1) }))) {
    termo.value = ''
    quantidade.value = '1'
    resultados.value = []
    campoBusca.value?.focus()
  }
}

function alterar(item, valor) {
  const url = `/consignacao/transferencias/${transferencia.value.id}/itens/${item.id}`
  return acao(() => api.put(url, { quantidade: String(Number(valor) || 0) }))
}

function confirmar() {
  $q.dialog({
    title: 'Senha do representante',
    message: `${transferencia.value.representante.cliente.nome} confirma que leva ${transferencia.value.itens.length} produto(s), ${formatarMoeda(transferencia.value.total)}.`,
    prompt: { model: '', type: 'password', isValid: (v) => !!v },
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Confirmar' },
  }).onOk(async (senha) => {
    const data = await acao(() => api.post(`/consignacao/transferencias/${transferencia.value.id}/confirmar`, { senha }))
    if (!data) return
    $q.notify({ type: 'positive', message: `Transferência ${data.numero} confirmada` })
    for (const aviso of data.avisos) $q.notify({ type: 'warning', message: aviso, timeout: 8000 })
    roteador.push({ name: 'comprovante-transferencia', params: { id: data.id }, query: { imprimir: 1 } })
  })
}

function descartar() {
  $q.dialog({
    title: 'Descartar a transferência',
    message: 'A transferência ainda não foi confirmada: não mexeu em nada e some.',
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Descartar', color: 'grey-8' },
  }).onOk(async () => {
    try {
      await api.delete(`/consignacao/transferencias/${transferencia.value.id}`)
      transferencia.value = null
      representanteId.value = null
      roteador.replace({ name: 'transferencia-nova' })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}

onMounted(async () => {
  if (!rota.params.id) return
  try {
    const { data } = await api.get(`/consignacao/transferencias/${rota.params.id}`)
    if (data.situacao !== 'aberta') return roteador.replace({ name: 'comprovante-transferencia', params: { id: data.id } })
    await mostrar(data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
})
</script>

<style scoped>
.campo-quantidade {
  max-width: 90px;
}
</style>
