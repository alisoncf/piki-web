<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Receber crediário</div>
      <q-chip v-if="sessaoCaixa" icon="point_of_sale" color="primary" text-color="white">{{ sessaoCaixa.nome }}</q-chip>
    </div>

    <q-banner v-if="semCaixa" class="bg-warning q-mb-md rounded-borders">
      <template #avatar><q-icon name="point_of_sale" /></template>
      {{ semCaixa }}
      <template #action><q-btn flat no-caps label="Ir para o caixa" :to="{ name: 'caixa' }" /></template>
    </q-banner>

    <section class="cartao q-pa-md q-mb-md">
      <q-select
        v-model="clienteId"
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
        @filter="buscarClientes"
        @update:model-value="carregarParcelas()"
      >
        <template #no-option><q-item><q-item-section class="text-suave">Digite parte do nome ou o CPF</q-item-section></q-item></template>
      </q-select>
    </section>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <template v-else-if="clienteId">
      <section class="cartao q-pa-md q-mb-md">
        <div class="row items-center q-mb-sm">
          <div class="formulario__secao col q-mb-none">Parcelas em aberto (todas as lojas)</div>
          <div class="text-caption text-suave">Juros sugeridos: {{ formatarPercentual(jurosAoMes) }} ao mês, por dia de atraso</div>
        </div>
        <div v-if="!parcelas.length" class="text-suave">Este cliente não tem parcelas em aberto.</div>
        <form v-if="parcelas.length" class="row q-col-gutter-sm items-center q-mb-sm" @submit.prevent="distribuir">
          <q-input
            v-model="valorADistribuir"
            outlined
            dense
            type="number"
            step="0.01"
            min="0"
            prefix="R$"
            label="Distribuir um valor"
            hint="Paga as parcelas da mais antiga para a mais nova; os juros são somados à parte"
            class="col-12 col-sm-5 col-md-3"
          />
          <div class="col-auto"><q-btn type="submit" flat no-caps color="primary" label="Distribuir" :disable="!(Number(valorADistribuir) > 0)" /></div>
        </form>
        <q-markup-table v-if="parcelas.length" flat dense separator="horizontal">
          <thead>
            <tr>
              <th></th>
              <th class="text-left">Documento</th>
              <th class="text-left">Parcela</th>
              <th class="text-left">Vencimento</th>
              <th class="text-right">Falta</th>
              <th class="text-right" style="width: 120px">Juros</th>
              <th class="text-right" style="width: 130px">Pagar</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in parcelas" :key="p.id" :class="{ 'text-suave': !p.marcada }">
              <td><q-checkbox v-model="p.marcada" dense :aria-label="`Pagar a parcela ${p.numero}/${p.parcelas}`" /></td>
              <td>
                {{ p.documento }}
                <q-badge v-if="p.origem !== 'venda'" outline color="grey-7" class="q-ml-xs">{{ p.origem === 'acerto' ? 'Acerto' : 'Avulsa' }}</q-badge>
              </td>
              <td>{{ p.numero }}/{{ p.parcelas }}</td>
              <td>
                {{ formatarDataHora(p.vencimento) }}
                <span v-if="p.dias_atraso" class="text-negative text-caption"> · {{ p.dias_atraso }} {{ p.dias_atraso === 1 ? 'dia' : 'dias' }} de atraso</span>
              </td>
              <td class="text-right">{{ formatarMoeda(p.aberto) }}</td>
              <td><q-input v-model="p.juros" dense outlined type="number" step="0.01" min="0" :disable="!p.marcada" :aria-label="`Juros da parcela ${p.numero}`" /></td>
              <td><q-input v-model="p.pagar" dense outlined type="number" step="0.01" min="0" :disable="!p.marcada" :aria-label="`Valor da parcela ${p.numero}`" /></td>
            </tr>
          </tbody>
        </q-markup-table>
      </section>

      <div v-if="parcelas.length" class="row q-col-gutter-md">
        <div class="col-12 col-md-7">
          <section class="cartao q-pa-md q-mb-md">
            <div class="row items-center q-mb-sm">
              <div class="formulario__secao col q-mb-none">Pagamento</div>
              <q-btn flat dense no-caps color="primary" icon="add" :label="pagamentos.length ? 'Outra forma' : 'Lançar pagamento'" @click="adicionar" />
            </div>
            <linhas-pagamento v-model:valor-recebido="valorRecebido" :linhas="pagamentos" :formas="formasAVista" :falta="faltaLancar" />
          </section>
        </div>
        <div class="col-12 col-md-5">
          <section class="cartao q-pa-md q-mb-md">
            <div class="row justify-between"><span>Parcelas</span><span>{{ formatarMoeda(principal) }}</span></div>
            <div class="row justify-between"><span>Juros</span><span>{{ formatarMoeda(juros) }}</span></div>
            <q-separator class="q-my-sm" />
            <div class="row justify-between text-h6"><span>Total</span><span>{{ formatarMoeda(total) }}</span></div>
            <div v-if="Math.abs(total - pago) >= 0.005" class="row justify-between text-weight-medium text-negative">
              <span>{{ pago < total ? 'Falta lançar' : 'Lançado a mais' }}</span><span>{{ formatarMoeda(Math.abs(total - pago)) }}</span>
            </div>
            <div v-if="troco > 0" class="row justify-between text-weight-medium"><span>Troco</span><span>{{ formatarMoeda(troco) }}</span></div>
            <q-btn
              unelevated
              no-caps
              color="primary"
              icon="point_of_sale"
              label="Confirmar recebimento"
              size="lg"
              class="full-width q-mt-md"
              :loading="enviando"
              :disable="!podeConfirmar"
              @click="confirmar"
            />
          </section>
        </div>
      </div>
    </template>

    <section v-if="ultimo" class="cartao q-pa-md q-mt-md">
      <div class="row items-center">
        <div class="col">
          <div class="text-weight-medium">Recebimento {{ ultimo.id }} · {{ ultimo.cliente.nome }} · {{ formatarMoeda(ultimo.total) }}</div>
          <div class="text-caption text-suave">
            <template v-if="ultimo.estornado_em">Estornado por {{ ultimo.estornado_por?.nome }}</template>
            <template v-else>{{ ultimo.pagamentos.map((pg) => `${pg.forma_pagamento.nome} ${formatarMoeda(pg.valor)}`).join(' · ') }}</template>
          </div>
        </div>
        <q-btn v-if="!ultimo.estornado_em" flat no-caps color="negative" icon="undo" label="Estornar" @click="estornar" />
      </div>
    </section>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import LinhasPagamento from '@/componentes/LinhasPagamento.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarMoeda } from '@/servicos/formatos'
import { centavos, completos, noDinheiro as somarDinheiro, novaLinha, somar, troco as calcularTroco } from '@/servicos/pagamentos'
import { useCaixaDaMaquinaStore } from '@/stores/caixaDaMaquina'

const $q = useQuasar()
const caixaDaMaquina = useCaixaDaMaquinaStore()

const sessaoCaixa = ref(null)
const semCaixa = ref('')
const formas = ref([])
const clientes = ref([])
const clienteId = ref(null)
const valorADistribuir = ref('')
const parcelas = ref([])
const jurosAoMes = ref('0')
const pagamentos = ref([])
const valorRecebido = ref('')
const carregando = ref(false)
const enviando = ref(false)
const ultimo = ref(null)

const formasAVista = computed(() => formas.value.filter((f) => f.tipo !== 'crediario'))
const marcadas = computed(() => parcelas.value.filter((p) => p.marcada))
const principal = computed(() => somar(marcadas.value.map((p) => ({ valor: p.pagar }))))
const juros = computed(() => somar(marcadas.value.map((p) => ({ valor: p.juros }))))
const total = computed(() => (centavos(principal.value) + centavos(juros.value)) / 100)
const pago = computed(() => somar(pagamentos.value))
const faltaLancar = computed(() => Math.max(0, centavos(total.value) - centavos(pago.value)) / 100)
const noDinheiro = computed(() => somarDinheiro(pagamentos.value, formas.value))
const troco = computed(() => calcularTroco(valorRecebido.value, noDinheiro.value))
const podeConfirmar = computed(() =>
  !!sessaoCaixa.value
  && marcadas.value.length > 0
  && marcadas.value.every((p) => Number(p.pagar) > 0 && centavos(p.pagar) <= centavos(p.aberto) && Number(p.juros || 0) >= 0)
  && pagamentos.value.length > 0
  && completos(pagamentos.value, valorRecebido.value, noDinheiro.value)
  && centavos(pago.value) === centavos(total.value),
)

function formatarPercentual(valor) {
  return `${Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`
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

/** As parcelas do cliente, já com os juros sugeridos; começam desmarcadas (menos as que vieram marcadas da
 * tela de contas a receber), com o que falta para pagar. */
async function carregarParcelas(marcar = []) {
  parcelas.value = []
  pagamentos.value = []
  valorRecebido.value = ''
  if (!clienteId.value) return
  carregando.value = true
  try {
    const { data } = await api.get(`/crediario/clientes/${clienteId.value}/parcelas`)
    jurosAoMes.value = data.juros_ao_mes
    parcelas.value = data.parcelas.map((p) => ({
      ...p, marcada: marcar.includes(p.id), pagar: Number(p.aberto).toFixed(2), juros: Number(p.juros).toFixed(2),
    }))
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

/** O valor que o cliente trouxe, distribuído da parcela mais antiga para a mais nova (como no VB6). */
function distribuir() {
  let resto = centavos(valorADistribuir.value)
  for (const p of parcelas.value) {
    const parte = Math.min(resto, centavos(p.aberto))
    p.marcada = parte > 0
    p.pagar = (parte > 0 ? parte / 100 : Number(p.aberto)).toFixed(2)
    resto -= parte
  }
  if (resto > 0) $q.notify({ type: 'warning', message: `Sobraram ${formatarMoeda(resto / 100)}: o valor passa do que o cliente deve` })
}

function adicionar() {
  pagamentos.value.push(novaLinha(pagamentos.value, formasAVista.value, faltaLancar.value))
}

async function confirmar() {
  enviando.value = true
  try {
    const { data } = await api.post('/crediario/recebimentos', {
      sessao_caixa_id: sessaoCaixa.value.id,
      cliente_id: clienteId.value,
      itens: marcadas.value.map((p) => ({ parcela_id: p.id, valor: Number(p.pagar).toFixed(2), juros: Number(p.juros || 0).toFixed(2) })),
      pagamentos: pagamentos.value.map((pg) => ({ forma_pagamento_id: pg.forma_pagamento_id, valor: Number(pg.valor).toFixed(2) })),
      valor_recebido: noDinheiro.value && valorRecebido.value ? Number(valorRecebido.value).toFixed(2) : null,
    })
    ultimo.value = data
    $q.notify({ type: 'positive', message: data.troco && Number(data.troco) ? `Recebido. Troco ${formatarMoeda(data.troco)}` : 'Recebido' })
    await carregarParcelas()
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    enviando.value = false
  }
}

function estornar() {
  $q.dialog({
    title: 'Estornar recebimento',
    message: 'As parcelas voltam a dever o que deviam, e os lançamentos saem do caixa.',
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Estornar', color: 'negative' },
  }).onOk(async () => {
    try {
      ultimo.value = (await api.post(`/crediario/recebimentos/${ultimo.value.id}/estornar`)).data
      if (clienteId.value === ultimo.value.cliente.id) await carregarParcelas()
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}

const rota = useRoute()

onMounted(async () => {
  // vindo da tela de contas a receber: o cliente e as parcelas já escolhidos
  if (rota.query.cliente) {
    clienteId.value = Number(rota.query.cliente)
    clientes.value = [{ id: clienteId.value, nome: rota.query.nome ?? '' }]
    carregarParcelas(String(rota.query.parcelas ?? '').split(',').filter(Boolean).map(Number))
  }
  try {
    const [f, c] = await Promise.all([api.get('/formas-pagamento', { params: { so_ativas: true } }), caixaDaMaquina.sessaoAberta()])
    formas.value = f.data
    sessaoCaixa.value = c.sessao ?? null
    semCaixa.value = c.aviso ?? ''
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
})
</script>
