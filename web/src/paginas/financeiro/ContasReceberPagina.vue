<template>
  <q-page padding>
    <div class="row items-center q-mb-md q-gutter-sm">
      <div class="piki-titulo col">Contas a receber</div>
      <template v-if="sessao.pode('receber.prejuizo') && selecionadas.length">
        <q-btn v-if="todasNoPrejuizo" flat no-caps icon="restore" label="Tirar do prejuízo" @click="tirarDoPrejuizo" />
        <q-btn v-else flat no-caps color="negative" icon="money_off" label="Pôr no prejuízo" @click="porNoPrejuizo" />
      </template>
      <q-btn
        v-if="sessao.pode('caixa.operar')"
        unelevated
        no-caps
        color="primary"
        icon="point_of_sale"
        :label="selecionadas.length ? `Receber ${selecionadas.length} selecionada${selecionadas.length > 1 ? 's' : ''}` : 'Receber selecionadas'"
        :disable="!selecionadas.length"
        @click="receberSelecionadas"
      />
    </div>

    <section class="cartao q-pa-md q-mb-md">
      <form class="row q-col-gutter-sm items-start" @submit.prevent="pesquisar">
        <q-btn-toggle
          v-model="filtros.situacao"
          no-caps
          unelevated
          toggle-color="primary"
          class="col-12 col-md-auto"
          :options="[{ label: 'Em aberto', value: 'aberto' }, { label: 'Já pagas', value: 'pagas' }, { label: 'Todas', value: 'todas' }]"
          @update:model-value="pesquisar"
        />
        <q-input v-model="filtros.busca" outlined dense clearable label="Cliente (nome ou CPF)" class="col-12 col-sm-6 col-md-3" />
        <q-input v-model="filtros.documento" outlined dense clearable label="Documento" class="col-6 col-sm-3 col-md-2" />
        <q-select
          v-model="filtros.loja"
          outlined
          dense
          clearable
          label="Loja"
          :options="sessao.empresas"
          option-value="id"
          :option-label="(e) => `${e.codigo} ${e.nome}`"
          emit-value
          map-options
          class="col-6 col-sm-3 col-md-2"
        />
        <q-select v-model="filtros.origem" outlined dense clearable label="Espécie" :options="ORIGENS" emit-value map-options class="col-6 col-sm-3 col-md-2" />

        <q-select v-model="filtros.data" outlined dense label="Data" :options="DATAS" emit-value map-options class="col-6 col-sm-3 col-md-2" />
        <q-input v-model="filtros.de" outlined dense type="date" stack-label label="De" class="col-6 col-sm-3 col-md-2" />
        <q-input v-model="filtros.ate" outlined dense type="date" stack-label label="Até" class="col-6 col-sm-3 col-md-2" />
        <q-select v-model="filtros.ordem" outlined dense label="Ordenar por" :options="ORDENS" emit-value map-options class="col-6 col-sm-3 col-md-2" @update:model-value="pesquisar" />
        <div class="col-12 col-md row items-center justify-end q-gutter-sm">
          <q-btn flat no-caps :icon="maisFiltros ? 'expand_less' : 'tune'" :label="maisFiltros ? 'Menos filtros' : 'Mais filtros'" @click="maisFiltros = !maisFiltros" />
          <q-btn flat no-caps label="Limpar" @click="limpar" />
          <q-btn type="submit" unelevated no-caps color="primary" icon="search" label="Pesquisar" />
        </div>

        <template v-if="maisFiltros">
          <q-input v-model="filtros.valor" outlined dense type="number" step="0.01" min="0" prefix="R$" label="Falta pagar (exato)" class="col-6 col-sm-3 col-md-2" />
          <q-input v-model="filtros.historico" outlined dense clearable label="Histórico" class="col-6 col-sm-3 col-md-3" />
          <selecao-cidade v-model="filtros.cidade_id" v-model:cidade="cidade" dense class="col-12 col-sm-6 col-md-3" />
          <q-select v-model="filtros.bloqueio" outlined dense clearable label="Cliente" :options="BLOQUEIO" emit-value map-options class="col-6 col-sm-3 col-md-2" />
          <q-select v-model="filtros.credito_suspenso" outlined dense clearable label="Crédito suspenso" :options="SIM_NAO" emit-value map-options class="col-6 col-sm-3 col-md-2" />
          <q-select v-model="filtros.prejuizo" outlined dense label="Prejuízo" :options="PREJUIZO" emit-value map-options class="col-6 col-sm-3 col-md-2" />
          <template v-if="listas.setores.length">
            <selecao-busca v-model="filtros.setor_id" :opcoes="listas.setores" :rotulo="nomeSetor" dense label="Setor" class="col-12 col-sm-6 col-md-3" />
            <selecao-busca v-model="filtros.orgao_id" :opcoes="listas.orgaos" dense label="Órgão" class="col-12 col-sm-6 col-md-3" />
            <q-select
              v-model="filtros.grupo_id"
              outlined
              dense
              clearable
              label="Grupo de clientes"
              :options="listas.grupos"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              class="col-12 col-sm-6 col-md-3"
            />
          </template>
        </template>
      </form>
    </section>

    <q-table
      v-model:pagination="paginacao"
      v-model:selected="selecionadas"
      flat
      bordered
      dense
      :rows="parcelas"
      :columns="colunas"
      row-key="id"
      selection="multiple"
      :loading="carregando"
      :rows-per-page-options="[50, 100, 200, 500]"
      rows-per-page-label="Por página"
      no-data-label="Nenhuma parcela com estes filtros"
      loading-label="Carregando..."
      @request="aoPaginar"
    >
      <template #top>
        <div class="row full-width items-center text-caption">
          <div class="col">
            {{ paginacao.rowsNumber }} parcela{{ paginacao.rowsNumber === 1 ? '' : 's' }} · valor {{ formatarMoeda(somas.valor) }} ·
            <strong>falta {{ formatarMoeda(somas.aberto) }}</strong>
          </div>
          <div v-if="selecionadas.length">
            Selecionadas: {{ selecionadas.length }} · falta {{ formatarMoeda(somaSelecionadas) }}
            <q-btn flat dense no-caps size="sm" label="Limpar seleção" @click="selecionadas = []" />
          </div>
        </div>
      </template>
      <template #body-cell-documento="props">
        <q-td :props="props">
          {{ props.row.documento }}
          <q-badge v-if="props.row.origem !== 'venda'" outline color="grey-7" class="q-ml-xs">{{ nomeOrigem(props.row.origem) }}</q-badge>
          <q-badge v-if="props.row.prejuizo" color="negative" class="q-ml-xs">
            Prejuízo
            <q-tooltip>
              {{ props.row.prejuizo_motivo }}<br />
              {{ formatarDataHora(props.row.prejuizo_em) }}<template v-if="props.row.prejuizo_por"> · {{ props.row.prejuizo_por }}</template>
            </q-tooltip>
          </q-badge>
          <div class="text-caption text-suave ellipsis" style="max-width: 220px">{{ props.row.historico }}</div>
        </q-td>
      </template>
      <template #body-cell-cliente="props">
        <q-td :props="props">
          <div>
            {{ props.row.cliente.nome }}
            <q-badge v-if="props.row.cliente.bloqueado" color="negative" class="q-ml-xs">Bloqueado</q-badge>
            <q-badge v-if="props.row.cliente.credito_suspenso" color="warning" text-color="dark" class="q-ml-xs">Suspenso</q-badge>
          </div>
          <div class="text-caption text-suave">
            {{ props.row.cliente.cpf_cnpj ? formatarDocumento(props.row.cliente.cpf_cnpj) : '' }}
            <template v-if="props.row.setor"> · {{ props.row.setor }}<template v-if="props.row.cidade"> ({{ props.row.cidade }})</template></template>
          </div>
        </q-td>
      </template>
      <template #body-cell-vencimento="props">
        <q-td :props="props">
          {{ formatarDataHora(props.row.vencimento) }}
          <div v-if="props.row.vencimento_inicial && props.row.vencimento_inicial !== props.row.vencimento" class="text-caption text-suave">
            inicial {{ formatarDataHora(props.row.vencimento_inicial) }}
          </div>
          <div v-if="props.row.dias_atraso && Number(props.row.aberto)" class="text-caption text-negative">{{ props.row.dias_atraso }} dias</div>
        </q-td>
      </template>
    </q-table>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
import SelecaoCidade from '@/componentes/SelecaoCidade.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarDocumento, formatarMoeda, nomeSetor } from '@/servicos/formatos'
import { centavos } from '@/servicos/pagamentos'
import { useSessaoStore } from '@/stores/sessao'

const ORIGENS = [
  { label: 'Venda', value: 'venda' },
  { label: 'Acerto de consignação', value: 'acerto' },
  { label: 'Avulsa', value: 'avulso' },
]
const DATAS = [
  { label: 'Vencimento', value: 'vencimento' },
  { label: 'Vencimento inicial', value: 'inicial' },
  { label: 'Emissão', value: 'emissao' },
]
const ORDENS = [
  { label: 'Vencimento', value: 'vencimento' },
  { label: 'Cliente', value: 'cliente' },
  { label: 'Documento', value: 'documento' },
  { label: 'Valor (maior primeiro)', value: 'valor' },
]
const BLOQUEIO = [
  { label: 'Só os bloqueados', value: 'bloqueados' },
  { label: 'Só os liberados', value: 'liberados' },
]
const SIM_NAO = [
  { label: 'Com crédito suspenso', value: true },
  { label: 'Sem crédito suspenso', value: false },
]
const PREJUIZO = [
  { label: 'Fora da lista', value: 'fora' },
  { label: 'Só as do prejuízo', value: 'so' },
  { label: 'Junto com as outras', value: 'junto' },
]
const VAZIOS = {
  situacao: 'aberto', busca: '', documento: '', loja: null, origem: null, data: 'vencimento', de: '', ate: '', ordem: 'vencimento',
  valor: '', historico: '', cidade_id: null, bloqueio: null, credito_suspenso: null, setor_id: null, orgao_id: null, grupo_id: null,
  prejuizo: 'fora',
}

const $q = useQuasar()
const roteador = useRouter()
const sessao = useSessaoStore()

const filtros = ref({ ...VAZIOS })
const cidade = ref(null)
const maisFiltros = ref(false)
const listas = ref({ setores: [], orgaos: [], grupos: [] })
const parcelas = ref([])
const selecionadas = ref([])
const somas = ref({ valor: 0, aberto: 0 })
const carregando = ref(false)
const paginacao = ref({ page: 1, rowsPerPage: 100, rowsNumber: 0 })

const nomeOrigem = (o) => ORIGENS.find((x) => x.value === o)?.label ?? o
const todasNoPrejuizo = computed(() => selecionadas.value.every((p) => p.prejuizo))
const somaSelecionadas = computed(() => selecionadas.value.reduce((s, p) => s + centavos(p.aberto), 0) / 100)

const colunas = [
  { name: 'documento', label: 'Documento', field: 'documento', align: 'left' },
  { name: 'cliente', label: 'Cliente', field: (p) => p.cliente.nome, align: 'left' },
  { name: 'parcela', label: 'Parcela', field: (p) => `${p.numero}/${p.parcelas}`, align: 'center' },
  { name: 'vencimento', label: 'Vencimento', field: 'vencimento', align: 'left' },
  { name: 'valor', label: 'Valor', field: 'valor', align: 'right', format: formatarMoeda },
  { name: 'aberto', label: 'Falta', field: 'aberto', align: 'right', format: formatarMoeda },
  { name: 'juros', label: 'Juros sug.', field: 'juros', align: 'right', format: (v) => (Number(v) ? formatarMoeda(v) : '') },
  { name: 'emissao', label: 'Emissão', field: 'emissao', align: 'left', format: formatarDataHora },
]

function parametros() {
  const params = {}
  for (const [chave, valor] of Object.entries(filtros.value)) {
    if (valor !== null && valor !== '' && valor !== undefined) params[chave] = typeof valor === 'string' ? valor.trim() : valor
  }
  const { page, rowsPerPage } = paginacao.value
  return { ...params, limite: rowsPerPage, deslocamento: (page - 1) * rowsPerPage }
}

async function carregar() {
  carregando.value = true
  try {
    const { data } = await api.get('/receber/parcelas', { params: parametros() })
    parcelas.value = data.itens
    somas.value = { valor: data.soma_valor, aberto: data.soma_aberto }
    paginacao.value = { ...paginacao.value, rowsNumber: data.total }
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function pesquisar() {
  paginacao.value = { ...paginacao.value, page: 1 }
  carregar()
}

function aoPaginar({ pagination }) {
  paginacao.value = { ...paginacao.value, page: pagination.page, rowsPerPage: pagination.rowsPerPage }
  carregar()
}

function limpar() {
  filtros.value = { ...VAZIOS }
  cidade.value = null
  pesquisar()
}

/** As selecionadas vão para a tela de receber; a baixa é de um cliente por vez, como no VB6. */
function receberSelecionadas() {
  const abertas = selecionadas.value.filter((p) => Number(p.aberto) > 0)
  const clientes = new Set(abertas.map((p) => p.cliente.id))
  if (!abertas.length) {
    $q.notify({ type: 'warning', message: 'As parcelas selecionadas já estão pagas' })
    return
  }
  if (clientes.size > 1) {
    $q.notify({ type: 'warning', message: 'Selecione as parcelas de um cliente só: o recebimento é de um cliente por vez' })
    return
  }
  const { cliente } = abertas[0]
  roteador.push({ name: 'receber-crediario', query: { cliente: cliente.id, nome: cliente.nome, parcelas: abertas.map((p) => p.id).join(',') } })
}

/** Prejuízo: a parcela que não se espera mais receber sai da lista; o cliente continua devendo. */
function porNoPrejuizo() {
  const abertas = selecionadas.value.filter((p) => Number(p.aberto) > 0 && !p.prejuizo)
  if (!abertas.length) {
    $q.notify({ type: 'warning', message: 'Nenhuma das selecionadas está em aberto fora do prejuízo' })
    return
  }
  $q.dialog({
    title: 'Pôr no prejuízo',
    message: `${abertas.length} parcela${abertas.length > 1 ? 's' : ''}, faltando ${formatarMoeda(abertas.reduce((s, p) => s + centavos(p.aberto), 0) / 100)}. `
      + 'Elas saem da lista do contas a receber, mas o cliente continua devendo. Por quê?',
    prompt: { model: '', type: 'text', outlined: true, isValid: (v) => !!v.trim() },
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Pôr no prejuízo', color: 'negative' },
  }).onOk((motivo) => mudarPrejuizo('/receber/prejuizo', { parcelas: abertas.map((p) => p.id), motivo }))
}

function tirarDoPrejuizo() {
  mudarPrejuizo('/receber/prejuizo/tirar', { parcelas: selecionadas.value.map((p) => p.id) })
}

async function mudarPrejuizo(url, pedido) {
  try {
    const { data } = await api.post(url, pedido)
    $q.notify({ type: 'positive', message: `${data.alteradas} parcela${data.alteradas === 1 ? '' : 's'} alterada${data.alteradas === 1 ? '' : 's'}` })
    selecionadas.value = []
    carregar()
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

onMounted(async () => {
  carregar()
  if (sessao.pode('clientes.ver')) {
    try {
      const [s, o, g] = await Promise.all(['/setores', '/orgaos', '/grupos-clientes'].map((url) => api.get(url)))
      listas.value = { setores: s.data, orgaos: o.data, grupos: g.data }
    } catch {
      // sem as listas, ficam só os outros filtros
    }
  }
})
</script>
