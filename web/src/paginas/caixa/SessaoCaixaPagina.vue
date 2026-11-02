<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'caixa' }" />
      <div class="piki-titulo col">{{ s?.caixa.nome ?? 'Caixa' }}</div>
      <q-badge v-if="s" :color="aberto ? 'positive' : 'grey'">{{ aberto ? 'Aberto' : 'Fechado' }}</q-badge>
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <template v-else-if="s">
      <section class="cartao q-pa-md q-mb-md">
        <div class="row q-col-gutter-md">
          <div class="col-12 col-sm-4">
            <div class="text-caption text-suave">Aberto</div>
            <div>{{ s.aberto_por.nome }} · {{ formatarDataHora(s.aberto_em) }}</div>
          </div>
          <div class="col-6 col-sm-3">
            <div class="text-caption text-suave">Fundo de troco</div>
            <div>{{ formatarMoeda(s.fundo) }}</div>
          </div>
          <div v-if="!aberto" class="col-6 col-sm-5">
            <div class="text-caption text-suave">Fechado</div>
            <div>{{ s.fechado_por?.nome }} · {{ formatarDataHora(s.fechado_em) }}</div>
          </div>
        </div>
        <div v-if="aberto && podeOperar" class="row q-gutter-sm q-mt-md">
          <q-btn unelevated no-caps color="positive" icon="add" label="Entrada" @click="novoLancamento('entrada')" />
          <q-btn unelevated no-caps color="negative" icon="remove" label="Saída" @click="novoLancamento('saida')" />
          <q-space />
          <q-btn outline no-caps color="primary" icon="lock" label="Fechar caixa" @click="pedirFechamento" />
        </div>
      </section>

      <section v-if="s.conferencia.length" class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Conferência do fechamento</div>
        <q-markup-table flat dense>
          <thead><tr><th class="text-left">Forma</th><th class="text-right">Esperado</th><th class="text-right">Contado</th><th class="text-right">Diferença</th></tr></thead>
          <tbody>
            <tr v-for="c in s.conferencia" :key="c.forma_pagamento.id">
              <td>{{ c.forma_pagamento.nome }}</td>
              <td class="text-right">{{ formatarMoeda(c.esperado) }}</td>
              <td class="text-right">{{ formatarMoeda(c.contado) }}</td>
              <td class="text-right text-weight-medium" :class="corDiferenca(c.diferenca)">{{ formatarMoeda(c.diferenca) }}</td>
            </tr>
          </tbody>
        </q-markup-table>
        <div v-if="s.observacao" class="q-mt-sm text-caption">Observação: {{ s.observacao }}</div>
      </section>

      <section v-else-if="s.totais" class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Saldo esperado</div>
        <div class="row q-col-gutter-md">
          <div v-for="t in s.totais" :key="t.forma_pagamento.id" class="col-6 col-sm-3">
            <div class="text-caption text-suave">{{ t.forma_pagamento.nome }}</div>
            <div class="text-h6">{{ formatarMoeda(t.saldo) }}</div>
          </div>
        </div>
      </section>

      <section class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Lançamentos</div>
        <q-table
          flat
          dense
          :rows="s.lancamentos.slice().reverse()"
          :columns="colunas"
          row-key="id"
          :pagination="{ rowsPerPage: 20 }"
          rows-per-page-label="Por página"
          no-data-label="Nenhum lançamento"
        >
          <template #body="props">
            <q-tr :props="props" :class="{ 'estornado': props.row.estornado_em }">
              <q-td key="hora" :props="props">{{ formatarDataHora(props.row.data_hora).slice(11) }}</q-td>
              <q-td key="motivo" :props="props">
                {{ props.row.descricao_motivo }}
                <div class="text-caption text-suave">
                  {{ [props.row.historico, props.row.funcionario?.nome, props.row.documento].filter(Boolean).join(' · ') }}
                </div>
              </q-td>
              <q-td key="forma" :props="props">{{ props.row.forma_pagamento.nome }}</q-td>
              <q-td key="valor" :props="props" :class="props.row.tipo === 'entrada' ? 'text-positive' : 'text-negative'">
                {{ props.row.tipo === 'entrada' ? '+' : '−' }} {{ formatarMoeda(props.row.valor) }}
              </q-td>
              <q-td key="quem" :props="props">
                {{ props.row.usuario.nome }}
                <div v-if="props.row.estornado_em" class="text-caption text-negative">Estornado por {{ props.row.estornado_por?.nome }}</div>
              </q-td>
              <q-td key="acoes" :props="props">
                <q-btn
                  v-if="aberto && podeOperar && !props.row.estornado_em && !props.row.documento"
                  flat
                  round
                  dense
                  size="sm"
                  icon="undo"
                  aria-label="Estornar"
                  @click="estornar(props.row)"
                >
                  <q-tooltip>Estornar (deixa de contar, mas fica na lista)</q-tooltip>
                </q-btn>
              </q-td>
            </q-tr>
          </template>
        </q-table>
      </section>
    </template>

    <q-dialog v-model="lancando">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="lancar">
          <q-card-section class="piki-titulo">{{ novo.tipo === 'entrada' ? 'Entrada' : 'Saída' }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-select v-model="novo.motivo" outlined label="Motivo *" :options="motivos" emit-value map-options />
            <q-input v-model="novo.valor" outlined autofocus type="number" step="0.01" min="0.01" prefix="R$" label="Valor *" :rules="[(v) => Number(v) > 0 || 'Informe o valor']" />
            <q-select v-model="novo.forma_pagamento_id" outlined label="Forma" :options="formas" option-value="id" option-label="nome" emit-value map-options />
            <selecao-busca
              v-if="['vale', 'comissao'].includes(novo.motivo)"
              v-model="novo.funcionario_id"
              :opcoes="funcionarios"
              label="Funcionário *"
              :rules="[(v) => !!v || 'Escolha o funcionário']"
            />
            <q-input v-model="novo.historico" outlined label="Histórico" maxlength="80" :hint="['despesa', 'outra_entrada'].includes(novo.motivo) ? 'Obrigatório: diga do que é' : ''" />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Lançar" :loading="salvando" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="fechando">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="fechar">
          <q-card-section class="piki-titulo">Fechar {{ s?.caixa.nome }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <div class="text-caption text-suave">Conte o que está no caixa e informe abaixo. A diferença aparece depois de fechar.</div>
            <q-input
              v-for="f in formasParaContar"
              :key="f.id"
              v-model="contagem[f.id]"
              outlined
              type="number"
              step="0.01"
              min="0"
              prefix="R$"
              :label="`${f.nome} contado`"
            />
            <q-input v-model="observacao" outlined type="textarea" autogrow label="Observação" maxlength="2000" />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Fechar caixa" :loading="salvando" />
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

import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarMoeda } from '@/servicos/formatos'
import { useCaixaDaMaquinaStore } from '@/stores/caixaDaMaquina'
import { useSessaoStore } from '@/stores/sessao'

const MOTIVOS = {
  entrada: [{ value: 'suprimento', label: 'Entrada de troco' }, { value: 'outra_entrada', label: 'Outra entrada' }],
  saida: [
    { value: 'sangria', label: 'Saída de troco ou retirada' }, { value: 'despesa', label: 'Despesa' },
    { value: 'vale', label: 'Vale de funcionário' }, { value: 'comissao', label: 'Comissão de cobrador' },
  ],
}

const $q = useQuasar()
const rota = useRoute()
const sessao = useSessaoStore()
const caixaDaMaquina = useCaixaDaMaquinaStore()

const s = ref(null)
const carregando = ref(true)
const salvando = ref(false)
const formas = ref([])
const funcionarios = ref([])
const lancando = ref(false)
const novo = ref({})
const fechando = ref(false)
const contagem = ref({})
const observacao = ref('')

const aberto = computed(() => s.value?.situacao === 'aberto')
const podeOperar = computed(() => sessao.pode('caixa.operar'))
const motivos = computed(() => MOTIVOS[novo.value.tipo] ?? [])
// a conferência é cega: pede a contagem do dinheiro e de cada forma que teve lançamento
const formasParaContar = computed(() => {
  const lista = formas.value.filter((f) => f.tipo === 'dinheiro').slice(0, 1)
  for (const l of s.value?.lancamentos ?? []) {
    if (!l.estornado_em && !lista.some((f) => f.id === l.forma_pagamento.id)) lista.push(l.forma_pagamento)
  }
  return lista
})

const colunas = [
  { name: 'hora', label: 'Hora', field: 'data_hora', align: 'left' },
  { name: 'motivo', label: 'Lançamento', field: 'descricao_motivo', align: 'left' },
  { name: 'forma', label: 'Forma', field: (l) => l.forma_pagamento.nome, align: 'left' },
  { name: 'valor', label: 'Valor', field: 'valor', align: 'right' },
  { name: 'quem', label: 'Quem', field: (l) => l.usuario.nome, align: 'left' },
  { name: 'acoes', label: '', field: 'id', align: 'right' },
]

function corDiferenca(valor) {
  const n = Number(valor)
  return n < 0 ? 'text-negative' : n > 0 ? 'text-warning' : 'text-positive'
}

async function carregar() {
  s.value = (await api.get(`/caixas/sessoes/${rota.params.id}`)).data
}

onMounted(async () => {
  try {
    const [, f] = await Promise.all([carregar(), api.get('/formas-pagamento', { params: { so_ativas: true } })])
    formas.value = f.data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

async function novoLancamento(tipo) {
  const dinheiro = formas.value.find((f) => f.tipo === 'dinheiro')
  novo.value = { tipo, motivo: MOTIVOS[tipo][0].value, valor: '', forma_pagamento_id: dinheiro?.id ?? null, historico: '', funcionario_id: null }
  lancando.value = true
  if (!funcionarios.value.length) {
    try {
      funcionarios.value = (await api.get('/funcionarios', { params: { so_ativos: true } })).data
    } catch {
      /* sem a lista, o vale não sai */
    }
  }
}

async function lancar() {
  salvando.value = true
  try {
    const { tipo, ...dados } = novo.value
    const { data } = await api.post(`/caixas/sessoes/${s.value.id}/lancamentos`, {
      ...dados, valor: String(dados.valor), historico: dados.historico || null,
      funcionario_id: ['vale', 'comissao'].includes(dados.motivo) ? dados.funcionario_id : null,
    })
    s.value.lancamentos.push(data)
    lancando.value = false
    if (s.value.totais) await carregar() // quem confere vê o saldo mudar
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

function estornar(lancamento) {
  $q.dialog({
    title: 'Estornar lançamento',
    message: `Estornar ${lancamento.descricao_motivo.toLowerCase()} de ${formatarMoeda(lancamento.valor)}? Ele deixa de contar no caixa, mas continua na lista.`,
    cancel: { flat: true, label: 'Não' },
    ok: { label: 'Estornar', color: 'negative' },
  }).onOk(async () => {
    try {
      const { data } = await api.post(`/caixas/sessoes/${s.value.id}/lancamentos/${lancamento.id}/estornar`)
      s.value.lancamentos = s.value.lancamentos.map((l) => (l.id === data.id ? data : l))
      if (s.value.totais) await carregar()
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}

function pedirFechamento() {
  contagem.value = {}
  observacao.value = ''
  fechando.value = true
}

async function fechar() {
  salvando.value = true
  try {
    const { data } = await api.post(`/caixas/sessoes/${s.value.id}/fechar`, {
      contagem: formasParaContar.value.map((f) => ({ forma_pagamento_id: f.id, contado: String(contagem.value[f.id] || '0') })),
      observacao: observacao.value || null,
    })
    s.value = data
    fechando.value = false
    if (caixaDaMaquina.caixa?.id === data.caixa.id) caixaDaMaquina.sair()
    const diferenca = data.conferencia.some((c) => Number(c.diferenca) !== 0)
    $q.notify({ type: diferenca ? 'warning' : 'positive', message: diferenca ? 'Caixa fechado com diferença' : 'Caixa fechado, sem diferença', timeout: 3000 })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}
</script>

<style scoped>
.estornado td {
  text-decoration: line-through;
  opacity: 0.6;
}
</style>
