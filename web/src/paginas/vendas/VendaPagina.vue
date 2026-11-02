<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'vendas' }" />
      <div class="piki-titulo col">{{ venda ? `Venda ${venda.numero}` : 'Venda' }}</div>
      <template v-if="venda">
        <q-badge :color="CORES[venda.situacao]" class="q-mr-md">{{ SITUACOES[venda.situacao] }}</q-badge>
        <q-btn v-if="aberta && podeVender" flat no-caps color="negative" icon="close" label="Cancelar venda" @click="cancelar" />
        <q-btn v-if="aberta && podeReceber" unelevated no-caps color="primary" icon="point_of_sale" label="Receber" class="q-ml-sm" @click="abrirRecebimento" />
      </template>
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <div v-else-if="venda" class="row q-col-gutter-md">
      <div class="col-12 col-md-8">
        <section v-if="editavel" class="cartao q-pa-md q-mb-md">
          <form class="row q-col-gutter-sm items-start" @submit.prevent="procurar">
            <q-input
              ref="campoBusca"
              v-model="termo"
              outlined
              autofocus
              label="Código, código de barras ou nome do produto"
              :loading="procurando"
              class="col"
            >
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
              <q-item-section side>{{ formatarMoeda(p.preco_queima || p.preco_venda) }}</q-item-section>
            </q-item>
          </q-list>
        </section>

        <q-table
          flat
          bordered
          :rows="venda.itens"
          :columns="colunas"
          row-key="id"
          :pagination="{ rowsPerPage: 0 }"
          hide-pagination
          no-data-label="Nenhum item ainda"
        >
          <template #body-cell-descricao="props">
            <q-td :props="props">
              <div>{{ props.row.descricao }}</div>
              <div class="text-caption text-suave">{{ formatarCodigoProduto(props.row.produto.codigo) }}</div>
              <div v-if="falta(props.row)" class="text-caption text-negative">
                <q-icon name="warning" /> Estoque da loja: {{ formatarQuantidade(props.row.disponivel) }}
              </div>
            </q-td>
          </template>
          <template #body-cell-acoes="props">
            <q-td :props="props" auto-width>
              <template v-if="editavel">
                <q-btn flat round dense size="sm" icon="edit" aria-label="Alterar" @click="abrirItem(props.row)" />
                <q-btn flat round dense size="sm" icon="delete" aria-label="Tirar" @click="excluir(props.row)" />
              </template>
            </q-td>
          </template>
        </q-table>
      </div>

      <div class="col-12 col-md-4">
        <section class="cartao q-pa-md q-mb-md q-gutter-y-sm">
          <q-select
            v-model="cabecalho.cliente_id"
            outlined
            use-input
            input-debounce="300"
            clearable
            label="Cliente"
            :options="clientes"
            option-value="id"
            option-label="nome"
            emit-value
            map-options
            :readonly="!editavel"
            @filter="buscarClientes"
            @update:model-value="salvarCabecalho"
          >
            <template #no-option><q-item><q-item-section class="text-suave">Digite parte do nome ou o CPF</q-item-section></q-item></template>
          </q-select>
          <q-select
            v-model="cabecalho.forma_pagamento_id"
            outlined
            label="Forma de pagamento"
            :options="formas"
            option-value="id"
            :option-label="(f) => (Number(f.desconto) ? `${f.nome} (${formatarPercentual(f.desconto)} de desconto)` : f.nome)"
            emit-value
            map-options
            :readonly="!editavel"
            @update:model-value="trocarForma"
          />
          <q-select
            v-if="forma && forma.parcelas > 1"
            v-model="cabecalho.parcelas"
            outlined
            label="Parcelas"
            :options="parcelas"
            emit-value
            map-options
            :readonly="!editavel"
            @update:model-value="salvarCabecalho"
          />
          <q-input v-model="cabecalho.observacao" outlined label="Observação" maxlength="200" :readonly="!editavel" @change="salvarCabecalho" />
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="row justify-between"><span>Subtotal</span><span>{{ formatarMoeda(venda.subtotal) }}</span></div>
          <div class="row justify-between items-center">
            <span>
              Desconto <span v-if="Number(venda.desconto)" class="text-caption text-suave">({{ formatarPercentual(percentual) }})</span>
              <q-btn v-if="editavel && venda.itens.length" flat dense no-caps size="sm" color="primary" label="Dar desconto" @click="abrirDesconto" />
            </span>
            <span>{{ formatarMoeda(-venda.desconto) }}</span>
          </div>
          <q-separator class="q-my-sm" />
          <div class="row justify-between text-h6"><span>Total</span><span>{{ formatarMoeda(venda.total) }}</span></div>
          <div v-if="venda.parcelas > 1" class="text-right text-caption text-suave">
            {{ venda.parcelas }}x de {{ formatarMoeda(venda.total / venda.parcelas) }}
          </div>
          <div v-if="venda.desconto_autorizado_por" class="text-caption text-suave q-mt-sm">Desconto autorizado por {{ venda.desconto_autorizado_por.nome }}</div>
          <div v-if="venda.parcelas_autorizadas_por" class="text-caption text-suave">Parcelas autorizadas por {{ venda.parcelas_autorizadas_por.nome }}</div>
        </section>

        <section class="cartao q-pa-md text-caption">
          <div>Vendedor: {{ venda.vendedor.nome }} · {{ formatarDataHora(venda.criado_em) }}</div>
          <div v-if="aberta">Vence em {{ formatarDataHora(venda.vence_em).slice(0, 10) }}</div>
          <template v-if="venda.situacao === 'recebida'">
            <div>Recebida por {{ venda.recebida_por?.nome }} no {{ venda.sessao_caixa?.caixa.nome }} · {{ formatarDataHora(venda.recebida_em) }}</div>
            <div v-if="venda.troco !== null">Recebido {{ formatarMoeda(venda.valor_recebido) }} · troco {{ formatarMoeda(venda.troco) }}</div>
          </template>
          <div v-if="venda.situacao === 'cancelada'">
            Cancelada por {{ venda.cancelada_por?.nome }} · {{ formatarDataHora(venda.cancelada_em) }}: {{ venda.motivo_cancelamento }}
          </div>
        </section>
      </div>
    </div>

    <!-- alterar item -->
    <q-dialog v-model="item.aberto">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="salvarItem">
          <q-card-section class="piki-titulo">{{ item.descricao }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-input v-model="item.quantidade" outlined autofocus type="number" step="any" min="0" label="Quantidade *" />
            <q-input v-model="item.desconto" outlined type="number" step="0.01" min="0" prefix="R$" label="Desconto no item" />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Salvar" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- desconto no total -->
    <q-dialog v-model="desconto.aberto">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="darDesconto">
          <q-card-section class="piki-titulo">Desconto na venda</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-btn-toggle v-model="desconto.em" no-caps unelevated toggle-color="primary" :options="[{ label: '%', value: 'percentual' }, { label: 'R$', value: 'valor' }]" />
            <q-input v-model="desconto.valor" outlined autofocus type="number" step="0.01" min="0" :label="desconto.em === 'valor' ? 'Desconto em reais' : 'Desconto em %'" />
            <div class="text-caption text-suave">Vale para a venda toda e é dividido entre os itens, na proporção do valor de cada um.</div>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Aplicar" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- autorização de quem pode mais -->
    <q-dialog v-model="autorizacao.aberto" @hide="responderAutorizacao(null)">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="responderAutorizacao({ login: autorizacao.login, senha: autorizacao.senha })">
          <q-card-section class="piki-titulo">Autorização</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <div>{{ autorizacao.mensagem }}</div>
            <q-input v-model="autorizacao.login" outlined autofocus label="Login de quem autoriza" autocomplete="off" />
            <q-input v-model="autorizacao.senha" outlined type="password" label="Senha" autocomplete="new-password" />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Autorizar" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- receber no caixa -->
    <q-dialog v-model="recebimento.aberto">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="receber">
          <q-card-section class="piki-titulo">Receber {{ formatarMoeda(venda?.total) }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <div>{{ forma?.nome }}<template v-if="venda?.parcelas > 1"> em {{ venda.parcelas }}x</template></div>
            <q-select
              v-model="recebimento.sessao_caixa_id"
              outlined
              label="Caixa *"
              :options="caixasAbertos"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              :hint="caixasAbertos.length ? '' : 'Nenhum caixa aberto nesta loja'"
            />
            <template v-if="forma?.tipo === 'dinheiro'">
              <q-input v-model="recebimento.valor_recebido" outlined autofocus type="number" step="0.01" min="0" prefix="R$" label="Valor recebido" />
              <div v-if="troco > 0" class="text-h6">Troco {{ formatarMoeda(troco) }}</div>
            </template>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Receber" :loading="recebimento.enviando" :disable="!recebimento.sessao_caixa_id" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCodigoProduto, formatarDataHora, formatarMoeda, formatarQuantidade } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const SITUACOES = { aberta: 'Aberta', recebida: 'Recebida', cancelada: 'Cancelada', vencida: 'Vencida' }
const CORES = { aberta: 'warning', recebida: 'positive', cancelada: 'grey', vencida: 'grey-7' }
// o caixa em que esta máquina recebe (um caixa por ponto)
const CAIXA_DA_MAQUINA = 'piki.caixa'

const $q = useQuasar()
const rota = useRoute()
const sessao = useSessaoStore()

const venda = ref(null)
const carregando = ref(true)
const formas = ref([])
const clientes = ref([])
const cabecalho = ref({ cliente_id: null, forma_pagamento_id: null, parcelas: 1, observacao: '' })
const campoBusca = ref(null)
const termo = ref('')
const quantidade = ref('1')
const procurando = ref(false)
const resultados = ref([])
const item = ref({ aberto: false })
const desconto = ref({ aberto: false, em: 'percentual', valor: '' })
const autorizacao = ref({ aberto: false, mensagem: '', login: '', senha: '' })
const recebimento = ref({ aberto: false, sessao_caixa_id: null, valor_recebido: '', enviando: false })
const caixasAbertos = ref([])

const podeVender = computed(() => sessao.pode('vendas.vender'))
const podeReceber = computed(() => sessao.pode('caixa.operar'))
const aberta = computed(() => venda.value?.situacao === 'aberta')
const editavel = computed(() => aberta.value && podeVender.value)
const url = computed(() => `/vendas/${rota.params.id}`)
const forma = computed(() => formas.value.find((f) => f.id === venda.value?.forma_pagamento?.id) ?? null)
const parcelas = computed(() =>
  Array.from({ length: forma.value?.parcelas ?? 1 }, (_, i) => ({
    value: i + 1,
    label: i + 1 > forma.value.parcelas_sem_autorizacao ? `${i + 1}x (pede autorização)` : `${i + 1}x`,
  })),
)
const percentual = computed(() => (Number(venda.value?.subtotal) ? (Number(venda.value.desconto) * 100) / Number(venda.value.subtotal) : 0))
const troco = computed(() => Number(recebimento.value.valor_recebido || 0) - Number(venda.value?.total || 0))

const colunas = [
  { name: 'descricao', label: 'Produto', field: 'descricao', align: 'left' },
  { name: 'quantidade', label: 'Qtd.', field: 'quantidade', align: 'right', format: formatarQuantidade },
  { name: 'preco', label: 'Preço', field: 'preco', align: 'right', format: formatarMoeda },
  { name: 'desconto', label: 'Desconto', field: 'desconto', align: 'right', format: (v) => (Number(v) ? formatarMoeda(-v) : '') },
  { name: 'total', label: 'Total', field: 'total', align: 'right', format: formatarMoeda },
  { name: 'acoes', label: '', field: 'id' },
]

function formatarPercentual(valor) {
  return `${Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`
}

function falta(linha) {
  return aberta.value && linha.disponivel !== null && Number(linha.disponivel) < Number(linha.quantidade)
}

function mostrar(dados) {
  venda.value = dados
  cabecalho.value = {
    cliente_id: dados.cliente?.id ?? null,
    forma_pagamento_id: dados.forma_pagamento?.id ?? null,
    parcelas: dados.parcelas,
    observacao: dados.observacao ?? '',
  }
  if (dados.cliente && !clientes.value.some((c) => c.id === dados.cliente.id)) clientes.value = [dados.cliente, ...clientes.value]
}

// pedido de autorização: a tela espera o login e a senha (ou null, se desistir)
let aoAutorizar = null
function pedirAutorizacao(mensagem) {
  autorizacao.value = { aberto: true, mensagem, login: '', senha: '' }
  return new Promise((resolver) => (aoAutorizar = resolver))
}
function responderAutorizacao(resposta) {
  autorizacao.value.aberto = false
  aoAutorizar?.(resposta)
  aoAutorizar = null
}

/** Manda o pedido; se passar do limite, pede a autorização e manda de novo com ela. */
async function enviar(pedido) {
  let dados = null
  for (;;) {
    try {
      const { data } = await pedido(dados)
      mostrar(data)
      return true
    } catch (e) {
      if (e.response?.status === 403 && e.response.headers?.['x-pede-autorizacao']) {
        dados = await pedirAutorizacao(mensagemDeErro(e))
        if (dados) continue
      } else {
        $q.notify({ type: 'negative', message: mensagemDeErro(e) })
      }
      if (venda.value) mostrar(venda.value) // desfaz o que mudou na tela
      return false
    }
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
  const ok = await enviar((autorizacao) =>
    api.post(`${url.value}/itens`, { produto_id: produto.id, quantidade: String(quantidade.value || 1), autorizacao }),
  )
  if (ok) {
    termo.value = ''
    quantidade.value = '1'
    resultados.value = []
    campoBusca.value?.focus()
  }
}

function abrirItem(linha) {
  item.value = { aberto: true, id: linha.id, descricao: linha.descricao, quantidade: String(Number(linha.quantidade)), desconto: String(Number(linha.desconto)) }
}

async function salvarItem() {
  const { id, quantidade: qtd, desconto: valor } = item.value
  const ok = await enviar((autorizacao) => api.put(`${url.value}/itens/${id}`, { quantidade: String(qtd), desconto: String(valor || 0), autorizacao }))
  if (ok) item.value.aberto = false
}

function excluir(linha) {
  $q.dialog({
    title: 'Tirar item',
    message: `Tirar ${linha.descricao} da venda?`,
    cancel: { flat: true, label: 'Não' },
    ok: { label: 'Tirar', color: 'negative' },
  }).onOk(() => enviar(() => api.delete(`${url.value}/itens/${linha.id}`)))
}

function abrirDesconto() {
  desconto.value = { aberto: true, em: 'percentual', valor: '' }
}

async function darDesconto() {
  const { em, valor } = desconto.value
  const ok = await enviar((autorizacao) => api.post(`${url.value}/desconto`, { [em]: String(valor || 0), autorizacao }))
  if (ok) desconto.value.aberto = false
}

function salvarCabecalho() {
  const { cliente_id, forma_pagamento_id, parcelas: n, observacao } = cabecalho.value
  return enviar((autorizacao) => api.put(url.value, { cliente_id, forma_pagamento_id, parcelas: n, observacao, autorizacao }))
}

function trocarForma() {
  cabecalho.value.parcelas = 1
  salvarCabecalho()
}

function buscarClientes(texto, atualizar, cancelar) {
  if (texto.trim().length < 2) {
    cancelar()
    return
  }
  api
    .get('/clientes', { params: { busca: texto.trim(), limite: 20 } })
    .then(({ data }) => atualizar(() => (clientes.value = data.itens)))
    .catch(() => cancelar())
}

function cancelar() {
  $q.dialog({
    title: 'Cancelar venda',
    message: 'Por que a venda está sendo cancelada?',
    prompt: { model: '', type: 'text', outlined: true, isValid: (v) => !!v.trim() },
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Cancelar venda', color: 'negative' },
  }).onOk((motivo) => enviar(() => api.post(`${url.value}/cancelar`, { motivo })))
}

async function abrirRecebimento() {
  let lembrado = null
  try {
    lembrado = Number(localStorage.getItem(CAIXA_DA_MAQUINA)) || null
  } catch {
    // sem armazenamento local: escolhe o caixa toda vez
  }
  try {
    const { data } = await api.get('/caixas')
    caixasAbertos.value = data.filter((c) => c.sessao).map((c) => ({ id: c.sessao.id, caixa_id: c.id, nome: c.nome }))
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    return
  }
  const doLembrado = caixasAbertos.value.find((c) => c.caixa_id === lembrado)
  const unico = caixasAbertos.value.length === 1 ? caixasAbertos.value[0] : null
  recebimento.value = { aberto: true, sessao_caixa_id: (doLembrado ?? unico)?.id ?? null, valor_recebido: '', enviando: false }
}

async function receber() {
  const { sessao_caixa_id, valor_recebido } = recebimento.value
  recebimento.value.enviando = true
  try {
    const { data } = await api.post(`${url.value}/receber`, { sessao_caixa_id, valor_recebido: valor_recebido ? String(valor_recebido) : null })
    mostrar(data)
    recebimento.value.aberto = false
    try {
      localStorage.setItem(CAIXA_DA_MAQUINA, String(caixasAbertos.value.find((c) => c.id === sessao_caixa_id)?.caixa_id))
    } catch {
      // sem armazenamento local: tudo bem
    }
    $q.notify({ type: 'positive', message: data.troco && Number(data.troco) ? `Venda recebida. Troco ${formatarMoeda(data.troco)}` : 'Venda recebida' })
    for (const aviso of data.avisos) $q.notify({ type: 'warning', message: aviso, timeout: 8000 })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    recebimento.value.enviando = false
  }
}

onMounted(async () => {
  try {
    const [v, f] = await Promise.all([api.get(url.value), api.get('/formas-pagamento', { params: { so_ativas: true } })])
    formas.value = f.data
    mostrar(v.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>
