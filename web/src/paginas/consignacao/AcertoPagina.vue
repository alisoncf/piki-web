<template>
  <!-- o acerto do consignado (D30): o que o representante vendeu, para o cliente dele ou para ele mesmo; fecha no
       caixa do consignado, sem a senha do representante -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">{{ acerto ? `Acerto ${acerto.numero}` : 'Acerto do representante' }}</div>
      <q-btn flat no-caps icon="list" label="Acertos" :to="{ name: 'transferencias', query: { aba: 'acertos' } }" />
    </div>

    <section v-if="!acerto" class="cartao q-pa-md">
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
        <template #no-option><q-item><q-item-section class="text-suave">Digite ao menos duas letras ou o código</q-item-section></q-item></template>
      </q-select>
    </section>

    <div v-else class="row q-col-gutter-md">
      <div class="col-12 col-md-7">
        <q-banner v-if="acerto.representante.lembrete_acerto" class="bg-warning q-mb-md rounded-borders">
          <template #avatar><q-icon name="sticky_note_2" /></template>
          <div class="text-weight-medium">Lembrete do acerto</div>
          <div class="pre-linha">{{ acerto.representante.lembrete_acerto }}</div>
        </q-banner>
        <q-table
          flat
          bordered
          title="Com o representante"
          :rows="comEle"
          :columns="colunasComEle"
          row-key="id"
          :filter="filtro"
          :pagination="{ rowsPerPage: 15 }"
          no-data-label="Nada com o representante nesta loja"
          class="tabela-clicavel"
          @row-click="(_, i) => incluir(i)"
        >
          <template #top-right>
            <q-input v-model="filtro" dense outlined placeholder="Filtrar" clearable>
              <template #prepend><q-icon name="search" /></template>
            </q-input>
          </template>
        </q-table>
        <div class="text-caption text-suave q-mt-xs">Clique no item para acertar uma peça; o mesmo produto aparece uma vez por transferência.</div>

        <section class="cartao q-pa-md q-mt-md">
          <div class="text-weight-medium">{{ acerto.representante.codigo }} · {{ acerto.representante.cliente.nome }}</div>
          <q-list v-if="acerto.itens.length" dense separator class="q-mt-sm">
            <q-item v-for="item in acerto.itens" :key="item.id">
              <q-item-section>
                <q-item-label>{{ item.item_transferencia.descricao }}</q-item-label>
                <q-item-label caption>
                  Transferência {{ item.item_transferencia.transferencia.numero }} · {{ formatarMoeda(item.preco) }}
                  <template v-if="acerto.queima"> (queima)</template>
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-input :model-value="item.quantidade" dense outlined type="number" step="any" min="0" class="campo-quantidade" @change="(v) => alterarItem(item, v)" />
              </q-item-section>
              <q-item-section side><q-btn flat round dense icon="delete_outline" aria-label="Tirar" @click="alterarItem(item, 0)" /></q-item-section>
            </q-item>
          </q-list>
          <div v-else class="text-suave q-mt-sm">Nenhum produto ainda.</div>
        </section>
      </div>

      <div class="col-12 col-md-5">
        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Para quem</div>
          <q-btn-toggle
            :model-value="acerto.para"
            no-caps
            unelevated
            toggle-color="primary"
            :options="[{ label: 'Cliente do representante', value: 'cliente' }, { label: 'O próprio representante', value: 'representante' }]"
            @update:model-value="(v) => salvar({ para: v, pagamento: 'prazo', queima: false, tipo_comissao: null, cliente_id: null })"
          />
          <q-select
            v-if="acerto.para === 'cliente'"
            :model-value="acerto.cliente?.id ?? null"
            outlined
            dense
            use-input
            input-debounce="300"
            label="Cliente (nome ou CPF)"
            :options="clientes"
            option-value="id"
            :option-label="(c) => c?.nome ?? ''"
            emit-value
            map-options
            class="q-mt-sm"
            @filter="buscarClientes"
            @update:model-value="(v) => salvar({ cliente_id: v })"
          >
            <template #selected>
              <span v-if="acerto.cliente">{{ acerto.cliente.nome }}<span v-if="acerto.cliente.cpf_cnpj" class="text-suave"> · {{ formatarDocumento(acerto.cliente.cpf_cnpj) }}</span></span>
            </template>
            <template #no-option><q-item><q-item-section class="text-suave">Digite ao menos duas letras</q-item-section></q-item></template>
          </q-select>
          <template v-else>
            <div class="text-caption text-suave q-mt-xs">Ele assume a dívida, como se tivesse comprado: a comissão vira desconto.</div>
            <div class="row items-center q-gutter-sm q-mt-xs">
              <q-btn-toggle
                :model-value="acerto.pagamento"
                no-caps
                unelevated
                toggle-color="primary"
                :options="[{ label: 'A prazo', value: 'prazo' }, { label: 'À vista', value: 'vista' }]"
                @update:model-value="(v) => salvar({ pagamento: v, queima: false, tipo_comissao: null })"
              />
              <q-toggle
                :model-value="acerto.queima"
                label="Queima"
                :disable="acerto.pagamento !== 'vista'"
                @update:model-value="(v) => salvar({ queima: v })"
              >
                <q-tooltip>Só produtos em queima, pelo preço de queima; à vista</q-tooltip>
              </q-toggle>
            </div>
            <div v-if="acerto.representante.bloqueado && acerto.pagamento === 'prazo'" class="text-negative text-caption q-mt-xs">O representante está bloqueado: para ele, só à vista.</div>
          </template>
          <q-select
            v-if="!acerto.queima"
            :model-value="acerto.tipo_comissao"
            outlined
            dense
            :label="acerto.pagamento === 'vista' ? 'Como ele paga' : 'Tipo de cobrança'"
            :options="acerto.pagamento === 'vista' ? TIPOS_VISTA : TIPOS_COBRANCA"
            emit-value
            map-options
            class="q-mt-sm"
            @update:model-value="(v) => salvar({ tipo_comissao: v })"
          />
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Valores</div>
          <q-input
            :model-value="acerto.negociado"
            outlined
            dense
            type="number"
            step="0.01"
            prefix="R$"
            label="Valor negociado (o que ele vendeu)"
            :hint="acerto.para === 'cliente' ? 'O que passar do total pelo preço da transferência fica para ele' : ''"
            @change="(v) => salvar({ negociado: v === '' ? null : String(v) })"
          />
          <div class="linha-total q-mt-md"><span>Total pelo preço {{ acerto.queima ? 'de queima' : 'da transferência' }}</span><span>{{ formatarMoeda(acerto.total_inicial) }}</span></div>
          <div class="linha-total"><span>Diferença</span><span>{{ formatarMoeda(acerto.diferenca) }}</span></div>
          <div class="linha-total">
            <span>{{ acerto.para === 'representante' ? 'Desconto' : 'Comissão' }} ({{ formatarPercentual(acerto.percentual) }} · {{ acerto.nome_comissao }})</span>
            <span>{{ formatarMoeda(acerto.comissao) }}</span>
          </div>
          <div class="linha-total text-weight-bold text-subtitle1"><span>Valor do acerto</span><span>{{ formatarMoeda(acerto.valor) }}</span></div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">{{ acerto.pagamento === 'vista' ? 'Pagamento' : 'Carnê' }}</div>
          <div v-if="acerto.pagamento === 'prazo'" class="row q-col-gutter-sm q-mb-sm">
            <q-select
              :model-value="acerto.parcelas"
              outlined
              dense
              label="Parcelas"
              :options="opcoesParcelas"
              emit-value
              map-options
              class="col-5"
              @update:model-value="(v) => salvar({ parcelas: v })"
            />
            <q-input
              :model-value="acerto.primeiro_vencimento"
              outlined
              dense
              type="date"
              stack-label
              label="Primeiro vencimento"
              class="col-7"
              @change="(v) => salvar({ primeiro_vencimento: v || null })"
            />
            <div v-if="aPrazo > 0" class="col-12 text-caption text-suave">
              {{ acerto.parcelas }}x de {{ formatarMoeda(aPrazo / acerto.parcelas) }} no nome de {{ acerto.cliente?.nome ?? '...' }}
            </div>
          </div>

          <div v-if="!sessaoCaixa" class="text-warning text-caption q-mb-sm">{{ avisoCaixa || 'Procurando o caixa...' }}</div>
          <div v-else class="text-caption text-suave q-mb-sm">No caixa <strong>{{ sessaoCaixa.nome }}</strong></div>
          <template v-if="acerto.pagamento === 'vista' || pagamentos.length">
            <div v-if="acerto.pagamento === 'prazo'" class="text-caption text-suave q-mb-xs">Entrada</div>
            <linhas-pagamento :linhas="pagamentos" :formas="formas" :falta="falta" com-parcelas />
          </template>
          <q-btn flat dense no-caps color="primary" icon="add" :label="acerto.pagamento === 'vista' ? 'Outra forma' : 'Entrada'" @click="pagamentos.push(novaLinha(pagamentos, formas, falta))" />
        </section>

        <div class="column q-gutter-sm">
          <q-btn unelevated no-caps color="primary" icon="handshake" label="Confirmar o acerto" :disable="!podeConfirmar" :loading="confirmando" @click="confirmar" />
          <q-btn flat no-caps color="grey-8" icon="delete_outline" label="Descartar" @click="descartar" />
        </div>
      </div>
    </div>

    <dialogo-autorizacao :estado="autorizacao" @responder="responder" />
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DialogoAutorizacao from '@/componentes/DialogoAutorizacao.vue'
import LinhasPagamento from '@/componentes/LinhasPagamento.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { usarAutorizacao } from '@/servicos/autorizacao'
import { formatarCodigoProduto, formatarDataHora, formatarDocumento, formatarMoeda, formatarQuantidade } from '@/servicos/formatos'
import { centavos, novaLinha, somar } from '@/servicos/pagamentos'
import { useCaixaDaMaquinaStore } from '@/stores/caixaDaMaquina'

const TIPOS_COBRANCA = [
  { value: 'loja', label: 'Pagamento na loja' },
  { value: 'cliente', label: 'Cobrança no cliente' },
  { value: 'representante', label: 'Representante recebe' },
  { value: 'deposito', label: 'Depósito bancário' },
  { value: 'boleto', label: 'Boleto bancário' },
]
const TIPOS_VISTA = [
  { value: 'vista_dinheiro', label: 'Dinheiro ou PIX' },
  { value: 'vista_cartao', label: 'Cartão à vista' },
  { value: 'vista_parcelado', label: 'Cartão parcelado' },
]

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const caixaDaMaquina = useCaixaDaMaquinaStore()
const { autorizacao, responder, comAutorizacao } = usarAutorizacao()
const representantes = ref([])
const representanteId = ref(null)
const clientes = ref([])
const acerto = ref(null)
const comEle = ref([])
const filtro = ref('')
const formas = ref([])
const parcelasMaximas = ref(10)
const pagamentos = ref([])
const sessaoCaixa = ref(null)
const avisoCaixa = ref('')
const confirmando = ref(false)

const colunasComEle = [
  { name: 'produto', label: 'Produto', field: (i) => `${formatarCodigoProduto(i.produto.codigo)} · ${i.descricao}`, align: 'left' },
  { name: 'transferencia', label: 'Transferência', field: (i) => `${i.transferencia.numero} · ${formatarDataHora(i.transferencia.confirmada_em).slice(0, 10)}`, align: 'left' },
  { name: 'preco', label: 'Preço', field: 'preco', format: formatarMoeda, align: 'right' },
  { name: 'restante', label: 'Resta', field: 'restante', format: formatarQuantidade, align: 'right' },
]

const formatarPercentual = (v) => `${Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`
const opcoesParcelas = computed(() => Array.from({ length: parcelasMaximas.value }, (_, i) => ({ value: i + 1, label: `${i + 1}x` })))
const pago = computed(() => somar(pagamentos.value))
const aPrazo = computed(() => (acerto.value?.pagamento === 'prazo' ? (centavos(acerto.value.valor) - centavos(pago.value)) / 100 : 0))
const falta = computed(() => (acerto.value?.pagamento === 'vista' ? (centavos(acerto.value.valor) - centavos(pago.value)) / 100 : 0))
const podeConfirmar = computed(() => {
  const a = acerto.value
  if (!a || !a.itens.length || !a.cliente || !sessaoCaixa.value || Number(a.valor) <= 0) return false
  if (pagamentos.value.some((pg) => !pg.forma_pagamento_id || !(Number(pg.valor) > 0))) return false
  return a.pagamento === 'vista' ? falta.value === 0 : !!a.primeiro_vencimento && aPrazo.value > 0
})

// o à vista começa com uma linha, já com o valor; mudando o jeito de pagar, recomeça
watch(
  () => acerto.value && `${acerto.value.pagamento}:${acerto.value.tipo_comissao}`,
  (agora, antes) => {
    if (!acerto.value || agora === antes) return
    pagamentos.value = acerto.value.pagamento === 'vista' ? [novaLinha([], formas.value, Number(acerto.value.valor))] : []
  },
)

function buscarRepresentantes(texto, atualizar, cancelar) {
  if (texto.trim().length < 2 && !/^\d+$/.test(texto.trim())) return cancelar()
  api
    .get('/representantes', { params: { busca: texto.trim() } })
    .then(({ data }) => atualizar(() => (representantes.value = data)))
    .catch(() => cancelar())
}

function buscarClientes(texto, atualizar, cancelar) {
  if (texto.trim().length < 2) return cancelar()
  api
    .get('/clientes', { params: { busca: texto.trim(), limite: 20 } })
    .then(({ data }) => atualizar(() => (clientes.value = data.itens)))
    .catch(() => cancelar())
}

async function mostrar(dados) {
  acerto.value = dados
  if (rota.params.id !== String(dados.id)) roteador.replace({ name: 'acerto', params: { id: dados.id } })
  const [c, f, s] = await Promise.all([
    api.get(`/representantes/${dados.representante.id}/com-ele`),
    api.get('/formas-pagamento', { params: { so_ativas: true } }),
    caixaDaMaquina.sessaoAberta(),
  ])
  comEle.value = c.data
  formas.value = f.data.filter((x) => x.tipo !== 'crediario')
  parcelasMaximas.value = f.data.find((x) => x.tipo === 'crediario')?.parcelas ?? 10
  sessaoCaixa.value = s.sessao ?? null
  avisoCaixa.value = s.aviso ?? ''
  if (dados.pagamento === 'vista') pagamentos.value = [novaLinha([], formas.value, Number(dados.valor))]
}

async function acao(fazer) {
  try {
    const { data } = await fazer()
    acerto.value = data
    return data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e), timeout: 8000 })
    return null
  }
}

async function abrir(id) {
  if (!id) return
  try {
    await mostrar((await api.post('/consignacao/acertos', { representante_id: id })).data)
  } catch (e) {
    representanteId.value = null
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

function incluir(item) {
  return acao(() => api.post(`/consignacao/acertos/${acerto.value.id}/itens`, { item_transferencia_id: item.id, quantidade: '1' }))
}

function alterarItem(item, valor) {
  return acao(() => api.put(`/consignacao/acertos/${acerto.value.id}/itens/${item.id}`, { quantidade: String(Number(valor) || 0) }))
}

/** Manda tudo o que se escolhe no acerto, com a mudança. */
function salvar(mudanca) {
  const a = acerto.value
  const dados = {
    para: a.para,
    cliente_id: a.para === 'cliente' ? (a.cliente?.id ?? null) : null,
    queima: a.queima,
    pagamento: a.pagamento,
    tipo_comissao: a.tipo_comissao,
    negociado: null, // sem ele, fica a diferença que já tinha
    parcelas: a.parcelas,
    primeiro_vencimento: a.primeiro_vencimento,
    ...mudanca,
  }
  return acao(() => api.put(`/consignacao/acertos/${a.id}`, dados))
}

function confirmar() {
  const a = acerto.value
  const mensagem = a.pagamento === 'vista'
    ? `${a.representante.cliente.nome} paga ${formatarMoeda(a.valor)} à vista.`
    : `Carnê de ${formatarMoeda(aPrazo.value)} em ${a.parcelas}x no nome de ${a.cliente.nome}.`
  $q.dialog({
    title: `Confirmar o acerto ${a.numero}`,
    message: `${a.itens.length} produto(s). ${mensagem}`,
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Confirmar' },
  }).onOk(async () => {
    const corpo = {
      sessao_caixa_id: sessaoCaixa.value.id,
      pagamentos: pagamentos.value.map((pg) => ({ forma_pagamento_id: pg.forma_pagamento_id, valor: String(pg.valor), parcelas: pg.parcelas ?? 1 })),
    }
    confirmando.value = true
    let data
    try {
      // passando do limite de crédito, pede o login e a senha da gerência e manda de novo
      data = await comAutorizacao((autorizacao) => api.post(`/consignacao/acertos/${a.id}/confirmar`, { ...corpo, autorizacao }))
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e), timeout: 8000 })
      return
    } finally {
      confirmando.value = false
    }
    if (!data) return
    $q.notify({ type: 'positive', message: `Acerto ${data.numero} confirmado` })
    roteador.push({ name: 'comprovante-acerto', params: { id: data.id }, query: { imprimir: 1 } })
  })
}

function descartar() {
  $q.dialog({
    title: 'Descartar o acerto',
    message: 'O acerto ainda não foi confirmado: não mexeu em nada e some.',
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Descartar', color: 'grey-8' },
  }).onOk(async () => {
    try {
      await api.delete(`/consignacao/acertos/${acerto.value.id}`)
      acerto.value = null
      representanteId.value = null
      roteador.replace({ name: 'acerto-novo' })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}

onMounted(async () => {
  if (!rota.params.id) return
  try {
    const { data } = await api.get(`/consignacao/acertos/${rota.params.id}`)
    if (data.situacao !== 'aberta') return roteador.replace({ name: 'comprovante-acerto', params: { id: data.id } })
    await mostrar(data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
})
</script>

<style scoped>
.campo-quantidade {
  max-width: 80px;
}
.linha-total {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
}
.pre-linha {
  white-space: pre-line;
}
</style>
