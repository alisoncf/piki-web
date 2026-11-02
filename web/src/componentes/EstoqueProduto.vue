<template>
  <!-- o produto na loja ativa: saldo, reservado, localização, impostos e histórico (D24) -->
  <div>
    <div v-if="carregando" class="row justify-center q-pa-md"><q-spinner color="primary" size="30px" /></div>
    <template v-else>
      <div class="row q-col-gutter-md q-mb-md">
        <div v-for="n in numeros" :key="n.rotulo" class="col-4 col-sm-3">
          <div class="text-caption text-suave">{{ n.rotulo }}</div>
          <div class="text-h6" :class="{ 'text-negative': Number(n.valor) < 0 }">
            {{ formatarQuantidade(n.valor) }} <span class="text-caption">{{ unidade }}</span>
          </div>
        </div>
        <div v-if="podeAjustar" class="col-12 col-sm-3 self-center">
          <q-btn outline no-caps color="primary" icon="tune" label="Ajustar quantidade" @click="abrirAjuste" />
        </div>
      </div>
      <q-banner v-if="Number(estoque.quantidade) < 0" dense rounded class="bg-red-1 text-negative q-mb-md">
        <template #avatar><q-icon name="warning" /></template>
        Estoque negativo: saiu mais do que entrou. Confira com uma contagem.
      </q-banner>

      <div class="row q-col-gutter-md items-start">
        <q-input v-model="dados.localizacao" outlined label="Localização na loja" maxlength="30" :readonly="!podeEditar" class="col-12 col-sm-6 col-md-3" />
        <q-input v-model="dados.cst_csosn" outlined label="CST/CSOSN do ICMS" mask="###" :readonly="!podeEditar" hint="Do regime desta empresa" class="col-6 col-sm-3 col-md-2" />
        <q-input v-model="dados.cfop" outlined label="CFOP" mask="#.###" unmasked-value :readonly="!podeEditar" class="col-6 col-sm-3 col-md-2" />
        <q-input v-model="dados.aliquota_icms" outlined label="Alíquota de ICMS" type="number" step="0.01" min="0" max="100" suffix="%" :readonly="!podeEditar" class="col-6 col-sm-3 col-md-2" />
        <div v-if="podeEditar" class="col-6 col-sm-3 col-md-3">
          <q-btn unelevated no-caps color="primary" icon="check" label="Salvar dados da loja" :loading="salvando" @click="salvarDados" />
        </div>
      </div>

      <div class="formulario__secao q-mt-lg">Histórico</div>
      <q-table
        v-model:pagination="paginacao"
        flat
        bordered
        dense
        :rows="movimentos"
        :columns="colunas"
        row-key="id"
        :loading="carregandoMovimentos"
        :rows-per-page-options="[10, 20, 50]"
        rows-per-page-label="Por página"
        no-data-label="Nenhum movimento nesta loja"
        loading-label="Carregando..."
        @request="aoPaginar"
      >
        <template #body-cell-quantidade="props">
          <q-td :props="props" :class="Number(props.row.quantidade) < 0 ? 'text-negative' : 'text-positive'">
            <template v-if="Number(props.row.quantidade)">{{ sinal(props.row.quantidade) }}</template>
            <div v-if="Number(props.row.reservado)" class="text-caption text-suave">reservado {{ sinal(props.row.reservado) }}</div>
          </q-td>
        </template>
      </q-table>
    </template>

    <q-dialog v-model="ajustando">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="ajustar">
          <q-card-section class="piki-titulo">Ajustar quantidade</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <div class="text-caption text-suave">Informe a quantidade certa nesta loja (contando o que está com os representantes). O sistema registra a diferença.</div>
            <q-input
              v-model="ajuste.quantidade"
              outlined
              autofocus
              type="number"
              :step="fracionado ? '0.001' : '1'"
              label="Quantidade certa *"
              :suffix="unidade"
              :hint="diferenca"
              :rules="[(v) => v !== '' && v !== null || 'Informe a quantidade', (v) => fracionado || Number.isInteger(Number(v)) || 'Este produto não aceita fração']"
            />
            <q-input v-model="ajuste.motivo" outlined label="Motivo *" maxlength="200" :rules="[(v) => (v?.trim().length ?? 0) >= 3 || 'Diga o motivo do ajuste']" />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Ajustar" :loading="salvando" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarQuantidade } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const props = defineProps({
  produtoId: { type: Number, required: true },
  unidade: { type: String, default: 'UN' },
  fracionado: { type: Boolean, default: false },
})

const $q = useQuasar()
const sessao = useSessaoStore()
const base = `/produtos/${props.produtoId}/estoque`
const podeEditar = computed(() => sessao.pode('estoque.editar'))
const podeAjustar = computed(() => sessao.pode('estoque.ajustar'))

const carregando = ref(true)
const salvando = ref(false)
const estoque = ref({})
const dados = ref({})
const movimentos = ref([])
const carregandoMovimentos = ref(false)
const paginacao = ref({ page: 1, rowsPerPage: 10, rowsNumber: 0 })
const ajustando = ref(false)
const ajuste = ref({ quantidade: '', motivo: '' })

const numeros = computed(() => [
  { rotulo: 'Em estoque', valor: estoque.value.quantidade },
  { rotulo: 'Com representantes', valor: estoque.value.reservado },
  { rotulo: 'Disponível na loja', valor: estoque.value.disponivel },
])

const colunas = [
  { name: 'data', label: 'Data', field: 'data_hora', align: 'left', format: formatarDataHora },
  { name: 'tipo', label: 'Movimento', field: (m) => [m.descricao, m.documento].filter(Boolean).join(' · '), align: 'left' },
  { name: 'quantidade', label: 'Quantidade', field: 'quantidade', align: 'right' },
  { name: 'saldo', label: 'Saldo', field: 'saldo', align: 'right', format: formatarQuantidade },
  { name: 'usuario', label: 'Quem', field: (m) => m.usuario?.nome ?? '', align: 'left' },
  { name: 'observacao', label: 'Observação', field: 'observacao', align: 'left' },
]

const diferenca = computed(() => {
  const nova = Number(ajuste.value.quantidade)
  if (ajuste.value.quantidade === '' || Number.isNaN(nova)) return ''
  const d = nova - Number(estoque.value.quantidade)
  return d ? `Hoje: ${formatarQuantidade(estoque.value.quantidade)} · diferença ${sinal(d)}` : 'É a quantidade de hoje'
})

function sinal(valor) {
  const n = Number(valor)
  return `${n > 0 ? '+' : ''}${formatarQuantidade(n)}`
}

function mostrar(e) {
  estoque.value = e
  dados.value = { localizacao: e.localizacao ?? '', cst_csosn: e.cst_csosn ?? '', cfop: e.cfop ?? '', aliquota_icms: e.aliquota_icms }
}

async function carregarMovimentos() {
  carregandoMovimentos.value = true
  const { page, rowsPerPage } = paginacao.value
  try {
    const { data } = await api.get(`${base}/movimentos`, { params: { limite: rowsPerPage, deslocamento: (page - 1) * rowsPerPage } })
    movimentos.value = data.itens
    paginacao.value = { ...paginacao.value, rowsNumber: data.total }
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregandoMovimentos.value = false
  }
}

function aoPaginar({ pagination }) {
  paginacao.value = { ...paginacao.value, page: pagination.page, rowsPerPage: pagination.rowsPerPage }
  carregarMovimentos()
}

onMounted(async () => {
  try {
    mostrar((await api.get(base)).data)
    await carregarMovimentos()
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

async function salvarDados() {
  salvando.value = true
  try {
    const d = dados.value
    const corpo = {
      localizacao: d.localizacao || null,
      cst_csosn: d.cst_csosn || null,
      cfop: d.cfop || null,
      aliquota_icms: d.aliquota_icms === '' ? null : d.aliquota_icms,
    }
    mostrar((await api.put(base, corpo)).data)
    $q.notify({ type: 'positive', message: 'Dados da loja salvos', timeout: 1500 })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

function abrirAjuste() {
  ajuste.value = { quantidade: '', motivo: '' }
  ajustando.value = true
}

async function ajustar() {
  salvando.value = true
  try {
    const { data } = await api.post(`${base}/ajuste`, { quantidade: String(ajuste.value.quantidade), motivo: ajuste.value.motivo.trim() })
    mostrar(data)
    ajustando.value = false
    paginacao.value = { ...paginacao.value, page: 1 }
    await carregarMovimentos()
    $q.notify({
      type: Number(data.quantidade) < 0 ? 'warning' : 'positive',
      message: Number(data.quantidade) < 0 ? 'Estoque ajustado, mas ficou negativo' : 'Estoque ajustado',
      timeout: 2000,
    })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}
</script>
