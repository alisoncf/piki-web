<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'venda', params: { id: rota.params.id } }" />
      <div class="piki-titulo col">{{ venda ? `Receber a venda ${venda.numero}` : 'Receber' }}</div>
      <q-chip v-if="sessaoCaixa" icon="point_of_sale" color="primary" text-color="white">{{ sessaoCaixa.nome }}</q-chip>
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <template v-else-if="venda">
      <q-banner v-if="!sessaoCaixa" class="bg-warning q-mb-md rounded-borders">
        <template #avatar><q-icon name="point_of_sale" /></template>
        {{ semCaixa }}
        <template #action><q-btn flat no-caps label="Ir para o caixa" :to="{ name: 'caixa' }" /></template>
      </q-banner>
      <q-banner v-if="venda.situacao !== 'fechada'" class="bg-grey-3 q-mb-md rounded-borders">
        Esta venda está {{ venda.situacao }}: só a venda fechada pelo vendedor é recebida.
      </q-banner>

      <div class="row q-col-gutter-md">
        <div class="col-12 col-md-7">
          <section class="cartao q-pa-md q-mb-md q-gutter-y-sm">
            <div class="formulario__secao">Forma de pagamento da venda</div>
            <div class="row q-col-gutter-sm">
              <q-select
                :model-value="venda.forma_pagamento?.id"
                outlined
                label="Forma"
                :options="formas"
                option-value="id"
                :option-label="(f) => (Number(f.desconto) ? `${f.nome} (${formatarPercentual(f.desconto)} de desconto)` : f.nome)"
                emit-value
                map-options
                hint="Trocar a forma muda o desconto quando o da forma nova é outro"
                class="col"
                @update:model-value="trocarForma"
              />
              <q-select
                v-if="crediario"
                :model-value="venda.parcelas"
                outlined
                label="Parcelas"
                :options="opcoesParcelas(forma)"
                emit-value
                map-options
                class="col-4"
                @update:model-value="trocarParcelas"
              />
            </div>
          </section>

          <section class="cartao q-pa-md q-mb-md">
            <div class="row items-center q-mb-sm">
              <div class="formulario__secao col q-mb-none">{{ crediario ? 'Entrada (o que o cliente paga agora)' : 'Pagamento' }}</div>
              <q-btn flat dense no-caps color="primary" icon="add" :label="crediario ? 'Lançar entrada' : 'Outra forma'" @click="adicionar" />
            </div>
            <div v-if="!pagamentos.length" class="text-caption text-suave q-mb-sm">
              {{ crediario ? 'Sem entrada: a venda toda vai para o carnê.' : 'Lance como o cliente vai pagar.' }}
            </div>
            <linhas-pagamento v-model:valor-recebido="valorRecebido" :linhas="pagamentos" :formas="formasAVista" :falta="faltaLancar" com-parcelas />
          </section>

          <section v-if="crediario" class="cartao q-pa-md q-mb-md">
            <div class="formulario__secao">Crediário</div>
            <div class="row q-col-gutter-sm q-mb-sm">
              <q-input
                v-model="dataBase"
                outlined
                dense
                type="date"
                stack-label
                label="Data base"
                hint="A 1ª parcela vence um mês depois dela"
                class="col-12 col-sm-6"
              />
              <q-select
                v-model="tipoCobranca"
                outlined
                dense
                label="Tipo de cobrança *"
                hint="Como o cliente vai pagar"
                :options="TIPOS_COBRANCA"
                emit-value
                map-options
                class="col-12 col-sm-6"
              />
            </div>
            <div v-if="venda.credito" class="text-caption q-mb-sm" :class="{ 'text-negative': passaDoLimite }">
              <template v-if="venda.credito.impedimento">{{ venda.credito.impedimento }}</template>
              <template v-else>
                Disponível no crédito do cliente: {{ formatarMoeda(venda.credito.disponivel) }}
                <span v-if="passaDoLimite"> · passa do disponível: vai pedir a autorização da gerência</span>
              </template>
            </div>
            <div v-for="p in previa" :key="p.numero" class="row justify-between text-caption">
              <span>{{ p.numero }}/{{ previa.length }} · vence {{ p.vencimento }}</span><span>{{ formatarMoeda(p.valor) }}</span>
            </div>
          </section>

          <section class="cartao q-pa-md q-mb-md">
            <div class="formulario__secao">Nota fiscal</div>
            <q-btn-toggle
              v-model="modeloNota"
              no-caps
              unelevated
              toggle-color="primary"
              :options="[{ label: 'NFC-e (65)', value: '65' }, { label: 'NF-e (55)', value: '55' }]"
            />
            <div class="text-caption text-suave q-mt-xs">A emissão ainda não está pronta; a escolha fica guardada na venda. A NF-e pede o cliente cadastrado.</div>
          </section>
        </div>

        <div class="col-12 col-md-5">
          <section class="cartao q-pa-md q-mb-md">
            <div class="text-weight-medium q-mb-sm">{{ venda.comprador ?? venda.cliente?.nome }}</div>
            <div class="row justify-between"><span>{{ venda.itens.length }} {{ venda.itens.length === 1 ? 'item' : 'itens' }}</span><span>{{ formatarMoeda(venda.subtotal) }}</span></div>
            <div v-if="Number(venda.desconto)" class="row justify-between"><span>Desconto</span><span>{{ formatarMoeda(-venda.desconto) }}</span></div>
            <div v-if="venda.entrega" class="row justify-between"><span>Entrega</span><span>{{ formatarMoeda(venda.taxa_entrega) }}</span></div>
            <q-separator class="q-my-sm" />
            <div class="row justify-between text-h6"><span>Total</span><span>{{ formatarMoeda(venda.total) }}</span></div>
            <div class="row justify-between"><span>{{ crediario ? 'Entrada' : 'Lançado' }}</span><span>{{ formatarMoeda(pago) }}</span></div>
            <div v-if="crediario" class="row justify-between text-weight-medium"><span>No carnê</span><span>{{ formatarMoeda(totalVenda - pago) }}</span></div>
            <div v-else-if="Math.abs(totalVenda - pago) >= 0.005" class="row justify-between text-weight-medium text-negative">
              <span>{{ pago < totalVenda ? 'Falta lançar' : 'Lançado a mais' }}</span><span>{{ formatarMoeda(Math.abs(totalVenda - pago)) }}</span>
            </div>
            <div v-if="troco > 0" class="row justify-between text-weight-medium"><span>Troco</span><span>{{ formatarMoeda(troco) }}</span></div>
            <q-btn
              unelevated
              no-caps
              color="primary"
              icon="point_of_sale"
              label="Confirmar recebimento"
              class="full-width q-mt-md"
              size="lg"
              :loading="enviando"
              :disable="!podeConfirmar"
              @click="confirmar"
            />
          </section>
        </div>
      </div>
    </template>

    <dialogo-autorizacao :estado="autorizacao" @responder="responderAutorizacao" />
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DialogoAutorizacao from '@/componentes/DialogoAutorizacao.vue'
import LinhasPagamento from '@/componentes/LinhasPagamento.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { usarAutorizacao } from '@/servicos/autorizacao'
import { formatarMoeda, TIPOS_COBRANCA } from '@/servicos/formatos'
import { centavos, completos, noDinheiro as somarDinheiro, novaLinha, somar, troco as calcularTroco } from '@/servicos/pagamentos'
import { useCaixaDaMaquinaStore } from '@/stores/caixaDaMaquina'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const caixaDaMaquina = useCaixaDaMaquinaStore()
const { autorizacao, responder: responderAutorizacao, comAutorizacao } = usarAutorizacao()

const venda = ref(null)
const formas = ref([])
const sessaoCaixa = ref(null) // { id (da sessão), nome (do caixa) }
const semCaixa = ref('')
const carregando = ref(true)
const enviando = ref(false)
const pagamentos = ref([])
const valorRecebido = ref('')
const dataBase = ref(hoje())
const modeloNota = ref('65')
const tipoCobranca = ref(null)

const url = computed(() => `/vendas/${rota.params.id}`)
const forma = computed(() => formaPorId(venda.value?.forma_pagamento?.id))
const crediario = computed(() => forma.value?.tipo === 'crediario')
const formasAVista = computed(() => formas.value.filter((f) => f.tipo !== 'crediario'))
const totalVenda = computed(() => Number(venda.value?.total || 0))
const pago = computed(() => somar(pagamentos.value))
const faltaLancar = computed(() => (crediario.value ? 0 : Math.max(0, centavos(totalVenda.value) - centavos(pago.value)) / 100))
const noDinheiro = computed(() => somarDinheiro(pagamentos.value, formas.value))
const troco = computed(() => calcularTroco(valorRecebido.value, noDinheiro.value))
const passaDoLimite = computed(() => !!venda.value?.credito && Number(venda.value.credito.disponivel) < totalVenda.value - pago.value)
const podeConfirmar = computed(() => {
  if (!sessaoCaixa.value || venda.value?.situacao !== 'fechada') return false
  if (!completos(pagamentos.value, valorRecebido.value, noDinheiro.value)) return false
  return crediario.value ? pago.value < totalVenda.value && !!dataBase.value : centavos(pago.value) === centavos(totalVenda.value)
})

/** As parcelas do carnê como vão sair: iguais, os centavos na última, um mês (o intervalo da forma) a partir da data base. */
const previa = computed(() => {
  if (!crediario.value || !dataBase.value) return []
  const n = venda.value.parcelas
  const total = centavos(totalVenda.value - pago.value)
  if (total <= 0) return []
  const parcela = Math.floor(total / n)
  const [ano, mes, dia] = dataBase.value.split('-').map(Number)
  const intervalo = forma.value?.intervalo ?? 30
  return Array.from({ length: n }, (_, i) => {
    let data
    if (intervalo % 30 === 0) {
      const meses = mes - 1 + ((i + 1) * intervalo) / 30
      const ultimo = new Date(ano, meses + 1, 0).getDate()
      data = new Date(ano, meses, Math.min(dia, ultimo))
    } else {
      data = new Date(ano, mes - 1, dia + (i + 1) * intervalo)
    }
    return { numero: i + 1, vencimento: data.toLocaleDateString('pt-BR'), valor: (i === n - 1 ? total - parcela * (n - 1) : parcela) / 100 }
  })
})

function hoje() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formaPorId(id) {
  return formas.value.find((f) => f.id === id) ?? null
}

function formatarPercentual(valor) {
  return `${Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`
}

function opcoesParcelas(f) {
  return Array.from({ length: f?.parcelas ?? 1 }, (_, i) => ({
    value: i + 1,
    label: i + 1 > f.parcelas_sem_autorizacao ? `${i + 1}x (pede autorização)` : `${i + 1}x`,
  }))
}

/** O que o caixa começa lançando: na forma da venda, o total; no crediário, nada (sem entrada). */
function pagamentosIniciais() {
  pagamentos.value = crediario.value || !forma.value
    ? []
    : [{ forma_pagamento_id: forma.value.id, valor: totalVenda.value.toFixed(2), parcelas: venda.value.parcelas }]
  valorRecebido.value = ''
  // o tipo de cobrança sugerido pela ficha do cliente; ele escolhe na hora
  tipoCobranca.value = venda.value?.cliente?.forma_cobranca === 'loja' ? 'loja' : 'cliente'
}

function adicionar() {
  pagamentos.value.push(novaLinha(pagamentos.value, formasAVista.value, faltaLancar.value))
}

async function mandar(pedido) {
  try {
    return await comAutorizacao(pedido)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    return null
  }
}

function trocarForma(id) {
  const nova = formaPorId(id)
  const antes = forma.value
  const mudaDesconto = !antes || Number(antes.desconto) !== Number(nova.desconto)
  const seguir = async () => {
    const data = await mandar((autorizacao) => api.post(`${url.value}/forma`, { forma_pagamento_id: id, parcelas: 1, autorizacao }))
    if (!data) return
    venda.value = data
    pagamentosIniciais()
  }
  // só pergunta quando um desconto que a venda tem vai mudar
  if (!mudaDesconto || !Number(venda.value.desconto)) return seguir()
  $q.dialog({
    title: 'Trocar a forma de pagamento',
    message: `O desconto da venda passa a ser o de ${nova.nome} (${formatarPercentual(nova.desconto)}), e o que tinha sido dado sai.`,
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Trocar' },
  }).onOk(seguir)
}

async function trocarParcelas(n) {
  const data = await mandar((autorizacao) => api.post(`${url.value}/forma`, { forma_pagamento_id: forma.value.id, parcelas: n, autorizacao }))
  if (data) venda.value = data
}

async function confirmar() {
  enviando.value = true
  const pedido = {
    sessao_caixa_id: sessaoCaixa.value.id,
    pagamentos: pagamentos.value.map((pg) => ({ forma_pagamento_id: pg.forma_pagamento_id, valor: Number(pg.valor).toFixed(2), parcelas: pg.parcelas })),
    valor_recebido: noDinheiro.value && valorRecebido.value ? Number(valorRecebido.value).toFixed(2) : null,
    data_base: crediario.value ? dataBase.value : null,
    tipo_cobranca: crediario.value ? tipoCobranca.value : null,
    modelo_nota: modeloNota.value,
  }
  const data = await mandar((autorizacao) => api.post(`${url.value}/receber`, { ...pedido, autorizacao }))
  enviando.value = false
  if (!data) return
  $q.notify({ type: 'positive', message: data.troco && Number(data.troco) ? `Venda recebida. Troco ${formatarMoeda(data.troco)}` : 'Venda recebida' })
  for (const aviso of data.avisos) $q.notify({ type: 'warning', message: aviso, timeout: 8000 })
  if (data.carne) {
    if (data.entrega) $q.notify({ type: 'info', message: 'Imprima também o canhoto de entrega, pela venda', timeout: 8000 })
    roteador.push({ name: 'carne', params: { id: data.id }, query: { imprimir: 1 } })
  } else if (data.entrega) roteador.push({ name: 'canhoto-entrega', params: { id: data.id }, query: { imprimir: 1 } })
  else roteador.push({ name: 'vendas' })
}

onMounted(async () => {
  try {
    const [v, f, c] = await Promise.all([api.get(url.value), api.get('/formas-pagamento', { params: { so_ativas: true } }), caixaDaMaquina.sessaoAberta()])
    formas.value = f.data
    sessaoCaixa.value = c.sessao ?? null
    semCaixa.value = c.aviso ?? ''
    venda.value = v.data
    pagamentosIniciais()
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>
