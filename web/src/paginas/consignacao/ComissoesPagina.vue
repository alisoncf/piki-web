<template>
  <!-- as comissões dos acertos (D30): o que ficou liberado no vencimento, o pagamento ao representante, que sai do
       caixa e deixa o resto de saldo, e os pagamentos já feitos -->
  <q-page class="q-pa-md">
    <div class="piki-titulo q-mb-md">Comissões dos representantes</div>

    <section class="cartao q-pa-md q-mb-md">
      <div class="row q-col-gutter-sm items-center">
        <q-select
          v-model="representante"
          outlined
          dense
          use-input
          input-debounce="300"
          label="Representante (nome, CPF ou código)"
          :options="representantes"
          option-value="id"
          :option-label="(r) => (r?.cliente ? `${r.codigo} · ${r.cliente.nome}` : '')"
          class="col-12 col-md-5"
          @filter="buscarRepresentantes"
          @update:model-value="carregar"
        >
          <template #no-option><q-item><q-item-section class="text-suave">Digite ao menos duas letras ou o código</q-item-section></q-item></template>
        </q-select>
        <q-input v-model="de" outlined dense type="date" stack-label label="Vencimento de" class="col-6 col-md-2" @update:model-value="carregar" />
        <q-input v-model="ate" outlined dense type="date" stack-label label="até" class="col-6 col-md-2" @update:model-value="carregar" />
        <q-toggle v-model="soAbertas" label="Só em aberto" class="col-12 col-md-auto" @update:model-value="carregar" />
      </div>
    </section>

    <template v-if="relatorio">
      <div class="row q-col-gutter-md q-mb-md">
        <div v-for="t in totais" :key="t.rotulo" class="col-6 col-md-3">
          <div class="cartao q-pa-md">
            <div class="text-caption text-suave">{{ t.rotulo }}</div>
            <div class="text-h6">{{ formatarMoeda(t.valor) }}</div>
          </div>
        </div>
      </div>

      <section v-if="podePagar" class="cartao q-pa-md q-mb-md">
        <div class="text-subtitle2 q-mb-sm">Pagar ao representante</div>
        <div v-if="avisoCaixa" class="text-negative">{{ avisoCaixa }}</div>
        <div v-else-if="caixaAberto" class="row q-col-gutter-sm items-center">
          <q-input v-model="valor" outlined dense type="number" step="0.01" min="0" label="Valor pago" class="col-6 col-md-2" />
          <q-select v-model="formaId" outlined dense emit-value map-options label="Forma" :options="formas" option-value="id" option-label="nome" class="col-6 col-md-3" />
          <div class="col-12 col-md-auto">
            <q-btn unelevated no-caps color="primary" icon="payments" label="Pagar" :loading="pagando" @click="pagar" />
          </div>
          <div class="col-12 text-caption text-suave">
            Sai do {{ caixaAberto.nome }}. Baixa as comissões liberadas {{ de || ate ? 'do período acima' : '' }}, das mais antigas para as mais novas; o que faltar fica de saldo.
          </div>
        </div>
      </section>

      <q-tabs v-model="aba" dense no-caps align="left" class="q-mb-sm">
        <q-tab name="comissoes" label="Comissões" />
        <q-tab name="pagamentos" label="Pagamentos" />
      </q-tabs>

      <q-table v-if="aba === 'comissoes'" flat bordered dense :rows="relatorio.linhas" :columns="colunas" row-key="id" :rows-per-page-options="[50, 100, 0]" no-data-label="Nenhuma comissão no filtro">
        <template #body-cell-situacao="p">
          <q-td :props="p"><q-badge :color="CORES[p.row.situacao]" :label="p.row.situacao" /></q-td>
        </template>
        <template #top-right>
          <span v-if="relatorio.quantas > relatorio.linhas.length" class="text-caption text-negative">
            Mostrando {{ relatorio.linhas.length }} de {{ relatorio.quantas }}: filtre o período. Os totais valem para o filtro todo.
          </span>
        </template>
      </q-table>

      <q-table v-else flat bordered dense :rows="pagamentos" :columns="colunasPagamentos" row-key="id" :rows-per-page-options="[50, 0]" no-data-label="Nenhum pagamento">
        <template #body-cell-acoes="p">
          <q-td :props="p">
            <q-badge v-if="p.row.estornado_em" color="negative" label="desfeito" class="q-mr-sm" />
            <q-btn flat dense no-caps color="primary" label="Comprovante" :to="{ name: 'comprovante-comissao', params: { id: p.row.id } }" />
            <q-btn v-if="podePagar && !p.row.estornado_em && !p.row.do_vb6" flat dense no-caps color="negative" label="Desfazer" @click="desfazer(p.row)" />
          </q-td>
        </template>
      </q-table>
    </template>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarMoeda } from '@/servicos/formatos'
import { useCaixaDaMaquinaStore } from '@/stores/caixaDaMaquina'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const roteador = useRouter()
const sessao = useSessaoStore()
const caixaDaMaquina = useCaixaDaMaquinaStore()
const podePagar = computed(() => sessao.pode('consignacao.pagar_comissao'))

const CORES = { aberta: 'warning', parcial: 'info', paga: 'positive' }
const FORMAS_ACEITAS = ['dinheiro', 'pix', 'deposito']
const data = (valor) => (valor ? formatarDataHora(valor).slice(0, 10) : '')
const moeda = (valor) => (valor === null || valor === undefined ? '' : formatarMoeda(valor))

const representantes = ref([])
const representante = ref(null)
const de = ref('')
const ate = ref('')
const soAbertas = ref(true)
const relatorio = ref(null)
const pagamentos = ref([])
const aba = ref('comissoes')
const formas = ref([])
const formaId = ref(null)
const valor = ref('')
const pagando = ref(false)
const caixaAberto = ref(null)
const avisoCaixa = ref('')

const colunas = [
  { name: 'acerto', label: 'Acerto', field: 'acerto', align: 'left' },
  { name: 'data_acerto', label: 'Data', field: 'data_acerto', format: data, align: 'left' },
  { name: 'cliente', label: 'Cliente', field: 'cliente', align: 'left' },
  { name: 'parcela', label: 'Parcela', field: 'parcela', align: 'left' },
  { name: 'vencimento', label: 'Vencimento', field: 'vencimento', format: data, align: 'left' },
  { name: 'valor_parcela', label: 'Vlr. parcela', field: 'valor_parcela', format: moeda, align: 'right' },
  { name: 'falta_na_parcela', label: 'Falta na parcela', field: 'falta_na_parcela', format: moeda, align: 'right' },
  { name: 'valor', label: 'Comissão', field: 'valor', format: moeda, align: 'right' },
  { name: 'pago', label: 'Pago', field: 'pago', format: moeda, align: 'right' },
  { name: 'liberada', label: 'Liberada', field: (l) => (l.liberada ? 'Sim' : 'A vencer'), align: 'left' },
  { name: 'situacao', label: 'Situação', field: 'situacao', align: 'left' },
]
const colunasPagamentos = [
  { name: 'data_hora', label: 'Data', field: 'data_hora', format: formatarDataHora, align: 'left' },
  { name: 'valor', label: 'Valor', field: 'valor', format: moeda, align: 'right' },
  { name: 'forma', label: 'Forma', field: (p) => p.forma ?? (p.do_vb6 ? 'No VB6' : ''), align: 'left' },
  { name: 'usuario', label: 'Pago por', field: 'usuario', align: 'left' },
  { name: 'acoes', label: '', field: 'id', align: 'right' },
]
const totais = computed(() => [
  { rotulo: 'Saldo liberado', valor: relatorio.value.liberado },
  { rotulo: 'A vencer', valor: relatorio.value.a_vencer },
  { rotulo: 'Já pago', valor: relatorio.value.pago },
  { rotulo: 'Comissão total', valor: relatorio.value.comissao },
])

function buscarRepresentantes(texto, atualizar, cancelar) {
  if (texto.trim().length < 2 && !/^\d+$/.test(texto.trim())) return cancelar()
  api
    .get('/representantes', { params: { busca: texto.trim() } })
    .then(({ data: lista }) => atualizar(() => (representantes.value = lista)))
    .catch(() => cancelar())
}

function periodo() {
  return { de: de.value || undefined, ate: ate.value || undefined }
}

async function prepararPagamento() {
  const situacao = await caixaDaMaquina.sessaoAberta()
  avisoCaixa.value = situacao.aviso ?? ''
  caixaAberto.value = situacao.sessao ?? null
  if (!formas.value.length) {
    formas.value = (await api.get('/formas-pagamento', { params: { so_ativas: true } })).data.filter((f) => FORMAS_ACEITAS.includes(f.tipo))
    formaId.value = (formas.value.find((f) => f.tipo === 'dinheiro') ?? formas.value[0])?.id ?? null
  }
}

async function carregar() {
  if (!representante.value) {
    relatorio.value = null
    return
  }
  try {
    const url = `/representantes/${representante.value.id}/comissoes`
    const [dados, feitos] = await Promise.all([
      api.get(url, { params: { ...periodo(), so_abertas: soAbertas.value } }),
      api.get(`${url}/pagamentos`),
    ])
    relatorio.value = dados.data
    pagamentos.value = feitos.data
    valor.value = Math.max(Number(dados.data.liberado), 0).toFixed(2)
    if (podePagar.value) await prepararPagamento()
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

function confirmar(mensagem, acao) {
  $q.dialog({ title: 'Confirmar', message: mensagem, cancel: { flat: true, label: 'Voltar', noCaps: true }, ok: { label: 'Confirmar', noCaps: true, unelevated: true } }).onOk(acao)
}

function pagar() {
  confirmar(`Pagar ${formatarMoeda(valor.value)} a ${representante.value.cliente.nome}, saindo do ${caixaAberto.value.nome}?`, async () => {
    pagando.value = true
    try {
      const { data: pagamento } = await api.post(`/representantes/${representante.value.id}/comissoes/pagamentos`, {
        valor: Number(valor.value).toFixed(2),
        forma_pagamento_id: formaId.value,
        sessao_caixa_id: caixaAberto.value.id,
        de: de.value || null,
        ate: ate.value || null,
      })
      roteador.push({ name: 'comprovante-comissao', params: { id: pagamento.id }, query: { imprimir: 1 } })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    } finally {
      pagando.value = false
    }
  })
}

function desfazer(pagamento) {
  confirmar(`Desfazer o pagamento de ${formatarMoeda(pagamento.valor)}? O valor volta ao caixa e as comissões voltam ao saldo.`, async () => {
    try {
      await api.post(`/consignacao/comissoes/pagamentos/${pagamento.id}/estornar`)
      await carregar()
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}
</script>
