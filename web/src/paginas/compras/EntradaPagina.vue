<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'entradas' }" />
      <div class="piki-titulo col">{{ nota ? `Nota ${nota.numero}/${nota.serie}` : 'Nota de entrada' }}</div>
      <q-badge v-if="nota" :color="aberta ? 'warning' : 'positive'">{{ aberta ? 'Aberta' : 'Confirmada' }}</q-badge>
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <template v-else-if="nota">
      <section class="cartao q-pa-md q-mb-md">
        <div class="row q-col-gutter-md">
          <div class="col-12 col-md-5">
            <div class="text-caption text-suave">Fornecedor</div>
            <router-link v-if="sessao.pode('fornecedores.ver')" :to="{ name: 'fornecedor', params: { id: nota.fornecedor.id } }" class="text-weight-medium">
              {{ nota.fornecedor.nome }}
            </router-link>
            <div v-else class="text-weight-medium">{{ nota.fornecedor.nome }}</div>
            <div class="text-caption">{{ formatarDocumento(nota.fornecedor.cpf_cnpj) }}</div>
          </div>
          <div class="col-6 col-md-2">
            <div class="text-caption text-suave">Emissão</div>
            <div>{{ formatarDataHora(nota.data_emissao) }}</div>
          </div>
          <div class="col-6 col-md-2">
            <div class="text-caption text-suave">Valor da nota</div>
            <div class="text-weight-medium">{{ formatarMoeda(nota.valor_total) }}</div>
          </div>
          <div class="col-12 col-md-3">
            <div class="text-caption text-suave">{{ aberta ? 'Carregada por' : 'Confirmada por' }}</div>
            <div>
              {{ aberta ? nota.usuario?.nome : nota.confirmada_por?.nome }}
              <span class="text-caption text-suave">{{ formatarDataHora(aberta ? nota.criado_em : nota.confirmada_em) }}</span>
            </div>
          </div>
          <div class="col-12 text-caption text-suave">
            Chave {{ nota.chave.replace(/(\d{4})(?=\d)/g, '$1 ') }}
            <q-btn flat dense no-caps size="sm" color="primary" icon="download" label="XML" @click="baixarXml" />
          </div>
        </div>
      </section>

      <div v-if="aberta" class="row items-center q-gutter-sm q-mb-md">
        <q-chip :color="faltam ? 'orange-2' : 'green-2'" :icon="faltam ? 'warning' : 'check'">
          {{ nota.itens.length - faltam }} de {{ nota.itens.length }} itens ligados a produtos
        </q-chip>
        <div v-if="faltam" class="text-caption text-suave">
          Cadastre os que faltam (ou ligue a um produto que já existe) e depois confirme a entrada.
        </div>
      </div>

      <section v-for="item in nota.itens" :key="item.id" class="cartao q-pa-md q-mb-sm item" :class="{ 'item--faltando': !item.produto }">
        <div class="row q-col-gutter-md items-start">
          <div class="col-12 col-md-5">
            <div class="text-weight-medium">{{ item.numero }}. {{ item.descricao }}</div>
            <div class="text-caption text-suave">
              Código {{ item.codigo }}<template v-if="item.ean"> · EAN {{ item.ean }}</template><template v-if="item.ncm"> · NCM {{ item.ncm }}</template>
            </div>
            <div class="text-caption">
              {{ formatarQuantidade(item.quantidade) }} {{ item.unidade }} × {{ formatarMoeda(item.valor_unitario) }} = {{ formatarMoeda(item.valor_produtos) }}
              <template v-if="Number(item.valor_custo) !== Number(item.valor_produtos)"> · com frete e impostos {{ formatarMoeda(item.valor_custo) }}</template>
            </div>
            <div class="q-mt-sm">
              <template v-if="item.produto">
                <q-chip dense square color="green-1" icon="link" class="q-ml-none">
                  {{ formatarCodigoProduto(item.produto.codigo) }} · {{ item.produto.nome }}
                </q-chip>
                <q-btn v-if="aberta && podeLancar" flat dense no-caps size="sm" color="primary" label="Trocar" @click="abrirLigacao(item)" />
              </template>
              <template v-else>
                <q-badge color="orange" class="q-mr-sm">Não cadastrado</q-badge>
                <template v-if="podeLancar">
                  <q-btn v-if="sessao.pode('produtos.editar')" flat dense no-caps size="sm" color="primary" icon="add" label="Cadastrar produto" @click="cadastrar(item)" />
                  <q-btn flat dense no-caps size="sm" color="primary" icon="link" label="Ligar a um produto" @click="abrirLigacao(item)" />
                </template>
              </template>
            </div>
          </div>

          <div class="col-6 col-md-2">
            <q-input
              :model-value="item.embalagem"
              outlined
              dense
              type="number"
              min="1"
              :label="`Unidades por ${item.unidade}`"
              :readonly="!aberta || !podeLancar || !item.produto"
              :hint="`Entram ${formatarQuantidade(item.unidades)} ${item.produto?.unidade ?? 'UN'}`"
              @change="(v) => salvarItem(item, { embalagem: Number(v) || 1 })"
            />
          </div>
          <div class="col-6 col-md-2">
            <div class="text-caption text-suave">Custo unitário</div>
            <div class="text-weight-medium">{{ formatarMoeda(item.custo_unitario) }}</div>
            <div v-if="item.produto" class="text-caption text-suave">antes {{ formatarMoeda(item.produto.custo) }}</div>
          </div>
          <div v-if="item.produto" class="col-12 col-md-3">
            <q-input
              :model-value="item.preco_venda ?? ''"
              outlined
              dense
              type="number"
              step="0.01"
              min="0"
              prefix="R$"
              label="Preço de venda novo"
              :readonly="!aberta || !podePrecos"
              :hint="`Hoje ${formatarMoeda(item.produto.preco_venda)}${sugerido(item) ? ` · pela margem ${formatarMoeda(sugerido(item))}` : ''}`"
              @change="(v) => salvarItem(item, { preco_venda: v === '' ? null : v })"
            >
              <template v-if="aberta && podePrecos && sugerido(item)" #after>
                <q-btn flat round dense icon="auto_fix_high" aria-label="Usar o preço pela margem" @click="salvarItem(item, { preco_venda: sugerido(item).toFixed(2) })">
                  <q-tooltip>Usar o preço pela margem</q-tooltip>
                </q-btn>
              </template>
            </q-input>
          </div>
        </div>
      </section>

      <div v-if="aberta && podeLancar" class="row justify-end q-gutter-sm q-my-md">
        <q-btn flat no-caps color="negative" icon="delete" label="Descartar nota" @click="descartar" />
        <q-btn
          color="primary"
          unelevated
          no-caps
          icon="check"
          label="Confirmar entrada"
          :disable="faltam > 0"
          :loading="confirmando"
          @click="confirmar"
        >
          <q-tooltip v-if="faltam">Ligue todos os itens a um produto</q-tooltip>
        </q-btn>
      </div>
    </template>

    <q-dialog v-model="ligando">
      <q-card class="cartao-estreito" style="width: 560px; max-width: 95vw">
        <q-card-section class="piki-titulo">Ligar a um produto</q-card-section>
        <q-card-section class="q-pt-none">
          <div class="text-caption text-suave q-mb-sm">{{ itemLigando?.descricao }}</div>
          <q-select
            v-model="produtoEscolhido"
            outlined
            autofocus
            use-input
            input-debounce="300"
            label="Código, código de barras ou nome do produto"
            :options="opcoesProduto"
            :option-label="(p) => `${formatarCodigoProduto(p.codigo)} · ${p.nome}`"
            option-value="id"
            @filter="buscarProdutos"
          >
            <template #no-option><q-item><q-item-section class="text-suave">Nenhum produto encontrado</q-item-section></q-item></template>
          </q-select>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-close-popup flat no-caps label="Cancelar" />
          <q-btn color="primary" unelevated no-caps label="Ligar" :disable="!produtoEscolhido" @click="ligar" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import {
  formatarCodigoProduto, formatarDataHora, formatarDocumento, formatarMoeda, formatarQuantidade,
} from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()

const nota = ref(null)
const carregando = ref(true)
const confirmando = ref(false)
const ligando = ref(false)
const itemLigando = ref(null)
const produtoEscolhido = ref(null)
const opcoesProduto = ref([])

const aberta = computed(() => nota.value?.situacao === 'aberta')
const podeLancar = computed(() => sessao.pode('entradas.lancar'))
const podePrecos = computed(() => podeLancar.value && sessao.pode('produtos.precos'))
const faltam = computed(() => nota.value?.itens.filter((i) => !i.produto).length ?? 0)

function sugerido(item) {
  const margem = Number(item.produto?.margem)
  const custo = Number(item.custo_unitario)
  return custo > 0 && margem > 0 ? Math.round(custo * (1 + margem / 100) * 100) / 100 : null
}

// ao abrir (e ao voltar do cadastro de um produto), a API liga sozinha os itens já cadastrados
onMounted(async () => {
  try {
    nota.value = (await api.get(`/entradas/${rota.params.id}`)).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

async function salvarItem(item, mudanca) {
  const dados = { produto_id: item.produto?.id ?? null, embalagem: item.embalagem, preco_venda: item.preco_venda, ...mudanca }
  try {
    const { data } = await api.put(`/entradas/${nota.value.id}/itens/${item.id}`, dados)
    nota.value.itens = nota.value.itens.map((i) => (i.id === item.id ? data : i))
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

function abrirLigacao(item) {
  itemLigando.value = item
  produtoEscolhido.value = null
  opcoesProduto.value = []
  ligando.value = true
}

function buscarProdutos(termo, atualizar, cancelar) {
  if (termo.trim().length < 2) {
    cancelar()
    return
  }
  api.get('/produtos', { params: { busca: termo.trim(), limite: 20 } })
    .then(({ data }) => atualizar(() => { opcoesProduto.value = data.itens }))
    .catch(() => cancelar())
}

async function ligar() {
  await salvarItem(itemLigando.value, { produto_id: produtoEscolhido.value.id })
  ligando.value = false
}

// atalho: a ficha de produto nova já vem com os dados do item; ao salvar, volta para cá
function cadastrar(item) {
  roteador.push({
    name: 'produto-novo',
    query: {
      nome: item.descricao, ncm: item.ncm ?? undefined, cest: item.cest ?? undefined, ean: item.ean ?? undefined,
      fornecedor: nota.value.fornecedor.id, codigo_fornecedor: item.codigo, volta: rota.fullPath,
    },
  })
}

function confirmar() {
  $q.dialog({
    title: 'Confirmar entrada',
    message: `Dar entrada dos ${nota.value.itens.length} itens no estoque de ${sessao.empresa?.nome}? O custo dos produtos passa a ser o desta nota.`,
    cancel: { flat: true, label: 'Não' },
    ok: { label: 'Confirmar' },
  }).onOk(async () => {
    confirmando.value = true
    try {
      nota.value = (await api.post(`/entradas/${nota.value.id}/confirmar`)).data
      $q.notify({ type: 'positive', message: 'Entrada confirmada', timeout: 2000 })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    } finally {
      confirmando.value = false
    }
  })
}

function descartar() {
  $q.dialog({
    title: 'Descartar nota',
    message: 'Descartar esta nota? Nada entra no estoque, e ela pode ser carregada de novo depois.',
    cancel: { flat: true, label: 'Não' },
    ok: { label: 'Descartar', color: 'negative' },
  }).onOk(async () => {
    try {
      await api.delete(`/entradas/${nota.value.id}`)
      await roteador.push({ name: 'entradas' })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}

async function baixarXml() {
  try {
    const { data } = await api.get(`/entradas/${nota.value.id}/xml`, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const link = Object.assign(document.createElement('a'), { href: url, download: `${nota.value.chave}.xml` })
    link.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}
</script>

<style scoped>
.item--faltando {
  border-left: 4px solid var(--q-warning);
}
</style>
