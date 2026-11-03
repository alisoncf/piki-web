<template>
  <q-page padding>
    <div class="row items-center q-mb-md q-gutter-sm">
      <div class="piki-titulo col">Contas a receber</div>
      <q-btn v-if="sessao.pode('receber.editar') && selecionadas.length" flat no-caps icon="event_repeat" label="Prorrogar" @click="abrirProrrogacao" />
      <q-btn v-if="sessao.pode('receber.cobranca') && selecionadas.length" flat no-caps icon="move_up" label="Mudar cobrança" @click="mudarCobranca" />
      <q-btn-dropdown v-if="podeBloquear && selecionadas.length" flat no-caps icon="person_off" label="Clientes">
        <q-list>
          <q-item v-close-popup clickable @click="bloquearClientes(true)"><q-item-section>Bloquear os clientes selecionados</q-item-section></q-item>
          <q-item v-close-popup clickable @click="bloquearClientes(false)"><q-item-section>Liberar os clientes selecionados</q-item-section></q-item>
        </q-list>
      </q-btn-dropdown>
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
        <q-select
          v-model="filtros.conta_cobranca_id"
          outlined
          dense
          clearable
          label="Cobrança"
          :options="contasCobranca"
          option-value="id"
          option-label="nome"
          emit-value
          map-options
          class="col-6 col-sm-3 col-md-2"
        />

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
          <q-select v-model="filtros.tipo_cobranca" outlined dense clearable label="Tipo de cobrança" :options="TIPOS_COBRANCA" emit-value map-options class="col-6 col-sm-3 col-md-2" />
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
      class="tabela-clicavel"
      @request="aoPaginar"
      @row-click="(_, p) => abrirParcela(p)"
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
          <div v-if="props.row.conta_cobranca !== 'Geral' || props.row.tipo_cobranca" class="text-caption">
            <template v-if="props.row.conta_cobranca !== 'Geral'"><q-icon name="contact_mail" size="14px" /> {{ props.row.conta_cobranca }}</template>
            <span v-if="props.row.tipo_cobranca" class="text-suave"> · {{ nomeTipoCobranca(props.row.tipo_cobranca) }}</span>
          </div>
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

    <!-- prorrogar as selecionadas -->
    <q-dialog v-model="prorrogacao.aberto">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="prorrogar">
          <q-card-section class="piki-titulo">Prorrogar {{ selecionadas.length }} parcela{{ selecionadas.length > 1 ? 's' : '' }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-btn-toggle v-model="prorrogacao.modo" no-caps unelevated toggle-color="primary" :options="[{ label: 'Para a data', value: 'data' }, { label: 'Mais dias', value: 'dias' }]" />
            <q-input v-if="prorrogacao.modo === 'data'" v-model="prorrogacao.vencimento" outlined type="date" stack-label label="Novo vencimento *" />
            <q-input v-else v-model="prorrogacao.dias" outlined type="number" min="1" label="Dias depois do vencimento de cada uma *" />
            <q-input v-model="prorrogacao.anotacao" outlined autogrow maxlength="500" label="Anotação do contato" hint="O que o cliente disse; fica no histórico da parcela" />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Prorrogar" :disable="prorrogacao.modo === 'data' ? !prorrogacao.vencimento : !(Number(prorrogacao.dias) > 0)" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- a parcela: tipo e conta de cobrança, o cabeçalho do documento e o histórico -->
    <q-dialog v-model="parcela.aberto">
      <q-card style="width: 640px; max-width: 95vw">
        <q-form @submit.prevent="salvarParcela">
          <q-card-section class="piki-titulo">{{ parcela.dados?.documento }} · parcela {{ parcela.dados?.numero }}/{{ parcela.dados?.parcelas }}</q-card-section>
          <q-card-section v-if="parcela.dados" class="q-pt-none">
            <div class="text-caption text-suave q-mb-sm">
              {{ parcela.dados.cliente.nome }} · vence {{ formatarDataHora(parcela.dados.vencimento) }} · valor {{ formatarMoeda(parcela.dados.valor) }} ·
              falta {{ formatarMoeda(parcela.dados.aberto) }} (só muda com a baixa)
            </div>
            <div class="row q-col-gutter-sm">
              <q-select v-model="parcela.tipo_cobranca" outlined dense clearable label="Tipo de cobrança" :options="TIPOS_COBRANCA" emit-value map-options :readonly="!podeEditar" class="col-12 col-sm-6" />
              <q-select
                v-model="parcela.conta_cobranca_id"
                outlined
                dense
                label="Conta de cobrança"
                :options="contasCobranca.filter((c) => c.ativo)"
                option-value="id"
                option-label="nome"
                emit-value
                map-options
                :readonly="!podeEditar"
                class="col-12 col-sm-6"
              />
              <q-input v-model="parcela.documento" outlined dense label="Número do documento" maxlength="20" :readonly="!podeEditar" class="col-12 col-sm-4" />
              <q-input v-model="parcela.historico" outlined dense label="Histórico do documento" maxlength="80" :readonly="!podeEditar" class="col-12 col-sm-8" hint="Vale para todas as parcelas do documento" />
            </div>
            <div class="formulario__secao q-mt-md">Histórico da parcela</div>
            <div v-if="!parcela.historico_lista.length" class="text-caption text-suave">Nenhuma mudança ainda.</div>
            <q-list v-else dense separator>
              <q-item v-for="(h, i) in parcela.historico_lista" :key="i">
                <q-item-section>
                  <q-item-label>{{ MUDANCAS[h.mudanca] ?? h.mudanca }}: {{ h.de ?? '—' }} → {{ h.para ?? '—' }}</q-item-label>
                  <q-item-label v-if="h.anotacao" caption>{{ h.anotacao }}</q-item-label>
                </q-item-section>
                <q-item-section side class="text-caption">{{ formatarDataHora(h.data_hora) }}<br />{{ h.usuario?.nome }}</q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Fechar" />
            <q-btn v-if="podeEditar" type="submit" color="primary" unelevated no-caps label="Salvar" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
import SelecaoCidade from '@/componentes/SelecaoCidade.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarDocumento, formatarMoeda, nomeSetor, nomeTipoCobranca, TIPOS_COBRANCA } from '@/servicos/formatos'
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
  conta_cobranca_id: null,
  tipo_cobranca: null,
}

const $q = useQuasar()
const roteador = useRouter()
const sessao = useSessaoStore()

const filtros = ref({ ...VAZIOS })
const cidade = ref(null)
const maisFiltros = ref(false)
const listas = ref({ setores: [], orgaos: [], grupos: [] })
const contasCobranca = ref([])
const prorrogacao = ref({ aberto: false, modo: 'data', vencimento: '', dias: '', anotacao: '' })
const parcela = ref({ aberto: false, dados: null, historico_lista: [] })
const podeEditar = computed(() => sessao.pode('receber.editar'))
const podeBloquear = computed(() => sessao.pode(['receber.cobranca', 'clientes.editar']))
const MUDANCAS = { prorrogacao: 'Prorrogação', cobranca: 'Conta de cobrança', tipo: 'Tipo de cobrança', prejuizo: 'Prejuízo', documento: 'Documento' }
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

function abrirProrrogacao() {
  prorrogacao.value = { aberto: true, modo: 'data', vencimento: '', dias: '', anotacao: '' }
}

/** Prorroga as selecionadas: para uma data só, ou tantos dias depois do vencimento de cada uma. */
async function prorrogar() {
  const { modo, vencimento, dias, anotacao } = prorrogacao.value
  try {
    const { data } = await api.post('/receber/prorrogar', {
      parcelas: selecionadas.value.map((p) => p.id),
      vencimento: modo === 'data' ? vencimento : null,
      dias: modo === 'dias' ? Number(dias) : null,
      anotacao: anotacao || null,
    })
    prorrogacao.value.aberto = false
    $q.notify({ type: 'positive', message: `${data.alteradas} parcela${data.alteradas === 1 ? '' : 's'} prorrogada${data.alteradas === 1 ? '' : 's'}` })
    selecionadas.value = []
    carregar()
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

async function abrirParcela(linha) {
  const conta = contasCobranca.value.find((c) => c.nome === linha.conta_cobranca)
  const numero = linha.numero_documento ?? ''
  parcela.value = {
    aberto: true, dados: linha, historico_lista: [], tipo_cobranca: linha.tipo_cobranca, conta_cobranca_id: conta?.id ?? null,
    documento: numero, historico: linha.historico, documentoAntes: numero, historicoAntes: linha.historico,
  }
  try {
    parcela.value.historico_lista = (await api.get(`/receber/parcelas/${linha.id}/historico`)).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

async function salvarParcela() {
  const p = parcela.value
  try {
    await api.put(`/receber/parcelas/${p.dados.id}`, { tipo_cobranca: p.tipo_cobranca, conta_cobranca_id: p.conta_cobranca_id })
    if (p.documento !== p.documentoAntes || p.historico !== p.historicoAntes) {
      await api.put(`/receber/documentos/${p.dados.conta_id}`, { historico: p.historico, documento: p.documento || null })
    }
    p.aberto = false
    $q.notify({ type: 'positive', message: 'Parcela salva' })
    carregar()
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

/** Bloqueia ou libera os clientes das selecionadas, de uma vez (o bloqueio por atraso é à mão). */
function bloquearClientes(bloquear) {
  const clientes = [...new Set(selecionadas.value.map((p) => p.cliente.id))]
  $q.dialog({
    title: bloquear ? 'Bloquear clientes' : 'Liberar clientes',
    message: `${bloquear ? 'Bloquear' : 'Liberar'} ${clientes.length} cliente${clientes.length > 1 ? 's' : ''}? Fica anotado na ficha de cada um.`,
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: bloquear ? 'Bloquear' : 'Liberar', color: bloquear ? 'negative' : 'primary' },
  }).onOk(async () => {
    try {
      const { data } = await api.post('/receber/clientes/bloqueio', { clientes, bloquear })
      $q.notify({ type: 'positive', message: `${data.alterados} cliente${data.alterados === 1 ? '' : 's'} ${bloquear ? 'bloqueado' : 'liberado'}${data.alterados === 1 ? '' : 's'}` })
      carregar()
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}

/** Muda as selecionadas de conta de cobrança: entregar ao cobrador, mandar ao advogado, voltar para a Geral... */
function mudarCobranca() {
  $q.dialog({
    title: 'Mudar cobrança',
    message: `Para onde vão as ${selecionadas.value.length} parcelas selecionadas?`,
    options: { type: 'radio', model: null, items: contasCobranca.value.filter((c) => c.ativo).map((c) => ({ label: c.nome, value: c.id })) },
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Mudar' },
  }).onOk(async (conta) => {
    if (!conta) return
    try {
      const { data } = await api.post('/receber/cobranca', { parcelas: selecionadas.value.map((p) => p.id), conta_cobranca_id: conta })
      $q.notify({ type: 'positive', message: `${data.alteradas} parcela${data.alteradas === 1 ? '' : 's'} mudada${data.alteradas === 1 ? '' : 's'}` })
      selecionadas.value = []
      carregar()
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
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
  api.get('/receber/contas-cobranca').then(({ data }) => (contasCobranca.value = data)).catch(() => {})
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
