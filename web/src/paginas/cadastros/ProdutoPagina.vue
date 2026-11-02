<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'produtos' }" />
      <div class="piki-titulo col">{{ novo ? 'Novo produto' : form.nome || 'Produto' }}</div>
      <q-badge v-if="!novo && !form.ativo" color="grey-6">Inativo</q-badge>
    </div>

    <indice-ficha v-if="!carregando" :key="secoes.length" :secoes="secoes" />
    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>

    <q-form v-else class="formulario" @submit.prevent="salvar">
      <fieldset :disabled="!podeEditar" class="sem-borda">
        <section id="secao-identificacao" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Identificação</div>
          <div class="row q-col-gutter-md">
            <q-input
              :model-value="novo ? 'Automático' : formatarCodigoProduto(codigo)"
              outlined
              readonly
              label="Código"
              hint="É também o código de barras interno"
              class="col-12 col-sm-4 col-md-2"
            />
            <q-input
              v-model="form.nome"
              outlined
              label="Nome *"
              maxlength="120"
              hint="O nome completo, com tamanho, medidas e marca"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
              class="col-12 col-sm-8 col-md-10"
            />
            <selecao-busca
              v-model="form.subsecao_id"
              :opcoes="opcoesSubsecao"
              label="Seção › subseção *"
              :rules="[(v) => !!v || 'Escolha a subseção']"
              class="col-12 col-md-5"
            />
            <selecao-busca v-model="form.marca_id" :opcoes="opcoesMarca" label="Marca" class="col-12 col-sm-6 col-md-3" />
            <q-select
              v-model="form.unidade"
              outlined
              label="Unidade *"
              :options="UNIDADES"
              use-input
              new-value-mode="add-unique"
              input-debounce="0"
              class="col-6 col-sm-3 col-md-2"
            />
            <div class="col-6 col-sm-3 col-md-2 column">
              <q-toggle v-model="form.fracionado" label="Aceita fração">
                <q-tooltip>Pode ser vendido com quantidade quebrada (2,5 m²)</q-tooltip>
              </q-toggle>
              <q-toggle v-model="form.ativo" label="Ativo" />
            </div>
          </div>
        </section>

        <section id="secao-preco" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Preço e custo</div>
          <div v-if="!podePrecos" class="text-caption text-suave q-mb-md">
            Você não tem permissão para mudar custo e preços (o mesmo em todas as lojas).
          </div>
          <div class="row q-col-gutter-md">
            <q-input v-model="form.custo" outlined label="Custo" type="number" step="0.01" min="0" prefix="R$" :readonly="!podePrecos" hint="O da última entrada" class="col-6 col-sm-3" />
            <q-input v-model="form.margem" outlined label="Margem" type="number" step="0.01" min="0" suffix="%" :readonly="!podePrecos" class="col-6 col-sm-3" />
            <q-input
              v-model="form.preco_venda"
              outlined
              label="Preço de venda"
              type="number"
              step="0.01"
              min="0"
              prefix="R$"
              :readonly="!podePrecos"
              :hint="sugerido ? `Pela margem: ${formatarMoeda(sugerido)}` : ''"
              class="col-6 col-sm-3"
            />
            <div class="col-6 col-sm-3">
              <q-toggle :model-value="emQueima" label="Em queima" :disable="!podePrecos" @update:model-value="alternarQueima" />
              <q-input
                v-if="emQueima"
                v-model="form.preco_queima"
                outlined
                dense
                label="Preço de queima"
                type="number"
                step="0.01"
                min="0"
                prefix="R$"
                :readonly="!podePrecos"
                :rules="[(v) => !v || Number(v) < Number(form.preco_venda) || 'Tem que ser menor que o preço de venda']"
              />
            </div>
          </div>
        </section>

        <section id="secao-barras" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Códigos de barras</div>
          <div class="text-caption text-suave q-mb-sm">
            O código {{ novo ? 'do produto' : formatarCodigoProduto(codigo) }} já serve de código de barras interno.
            Aqui vão os códigos de fábrica (EAN).
          </div>
          <div class="row items-center q-gutter-sm q-mb-sm">
            <q-chip v-for="(c, i) in form.codigos_barras" :key="c" :removable="podeEditar" icon="qr_code_2" @remove="form.codigos_barras.splice(i, 1)">
              {{ c }}
            </q-chip>
          </div>
          <q-input
            v-if="podeEditar"
            v-model="novoCodigo"
            outlined
            dense
            label="Acrescentar código (leia com o leitor ou digite e tecle Enter)"
            inputmode="numeric"
            maxlength="14"
            style="max-width: 420px"
            @keydown.enter.prevent="acrescentarCodigo"
          >
            <template #append><q-btn flat round dense icon="add" aria-label="Acrescentar código" @click="acrescentarCodigo" /></template>
          </q-input>
        </section>

        <section id="secao-fornecedores" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Fornecedores</div>
          <div class="text-caption text-suave q-mb-md">
            De quem a loja compra. O código do produto no fornecedor liga o item da nota de entrada a este produto.
          </div>
          <div v-for="(f, i) in form.fornecedores" :key="i" class="row q-col-gutter-md items-start q-mb-sm">
            <selecao-busca
              v-model="f.fornecedor_id"
              :opcoes="opcoesFornecedor"
              :rotulo="(o) => o.nome_fantasia || o.nome"
              label="Fornecedor *"
              :rules="[(v) => !!v || 'Escolha o fornecedor']"
              class="col-12 col-sm-7"
            />
            <q-input v-model="f.codigo" outlined label="Código no fornecedor" maxlength="60" class="col-10 col-sm-4" />
            <div class="col-2 col-sm-1">
              <q-btn flat round icon="delete_outline" color="grey-7" aria-label="Remover fornecedor" @click="form.fornecedores.splice(i, 1)" />
            </div>
          </div>
          <q-btn flat no-caps color="primary" icon="add" label="Adicionar fornecedor" @click="form.fornecedores.push({ fornecedor_id: null, codigo: '' })" />
        </section>

        <section id="secao-fiscal" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Fiscal</div>
          <div class="text-caption text-suave q-mb-md">Os impostos que dependem do regime de cada loja ficam no estoque da loja.</div>
          <div class="row q-col-gutter-md">
            <q-input v-model="form.ncm" outlined label="NCM" mask="####.##.##" unmasked-value class="col-6 col-sm-3" />
            <q-input v-model="form.cest" outlined label="CEST" mask="##.###.##" unmasked-value class="col-6 col-sm-3" />
            <q-select v-model="form.origem" outlined label="Origem" :options="ORIGENS" emit-value map-options class="col-12 col-sm-6" />
          </div>
        </section>

        <section v-if="!novo" id="secao-fotos" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Fotos</div>
          <fotos-produto v-model="fotos" :produto-id="Number(rota.params.id)" :pode-editar="podeEditar" />
        </section>

        <section id="secao-observacoes" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Observações</div>
          <q-input v-model="form.observacao" outlined type="textarea" autogrow maxlength="4000" />
        </section>
      </fieldset>

      <div v-if="podeEditar" class="formulario__acoes row justify-end q-gutter-sm q-mb-md">
        <q-btn flat no-caps label="Cancelar" :to="{ name: 'produtos' }" />
        <q-btn type="submit" color="primary" unelevated no-caps icon="check" label="Salvar" :loading="salvando" />
      </div>
    </q-form>

    <!-- fora do formulário do produto: o estoque é da loja e tem o seu próprio salvar -->
    <section v-if="!carregando && verEstoque" id="secao-estoque" class="cartao q-pa-md q-mb-md formulario">
      <div class="formulario__secao">Estoque em {{ sessao.empresa?.nome }}</div>
      <estoque-produto :produto-id="Number(rota.params.id)" :unidade="form.unidade" :fracionado="form.fracionado" />
    </section>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import EstoqueProduto from '@/componentes/EstoqueProduto.vue'
import FotosProduto from '@/componentes/FotosProduto.vue'
import IndiceFicha from '@/componentes/IndiceFicha.vue'
import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCodigoProduto, formatarMoeda, ORIGENS, soDigitos } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const UNIDADES = ['UN', 'JG', 'PC', 'KIT', 'PAR', 'CX', 'M', 'M2', 'KG']

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()

const novo = computed(() => !rota.params.id)
const podeEditar = computed(() => sessao.pode('produtos.editar'))
const podePrecos = computed(() => podeEditar.value && sessao.pode('produtos.precos'))
const verEstoque = computed(() => !novo.value && sessao.pode('estoque.ver'))
const carregando = ref(true)
const salvando = ref(false)
const codigo = ref(null)
const fotos = ref([])
const novoCodigo = ref('')

const listaSecoes = ref([])
const marcas = ref([])
const fornecedores = ref([])
// os que o produto já tem, para o campo mostrar o nome mesmo sem a lista completa
const fornecedoresDoProduto = ref([])
const subsecaoAtual = ref(null)
const marcaAtual = ref(null)

// a ficha é uma página só (sem abas); o índice leva a cada parte
const secoes = computed(() => [
  ['identificacao', 'Identificação'], ['preco', 'Preço e custo'], ['barras', 'Códigos de barras'],
  ['fornecedores', 'Fornecedores'], ['fiscal', 'Fiscal'], ...(novo.value ? [] : [['fotos', 'Fotos']]),
  ['observacoes', 'Observações'], ...(verEstoque.value ? [['estoque', 'Estoque']] : []),
].map(([id, titulo]) => ({ id: `secao-${id}`, titulo })))

function vazio() {
  return {
    nome: '', subsecao_id: null, marca_id: null, unidade: 'UN', fracionado: false,
    custo: '0', margem: '0', preco_venda: '0', preco_queima: null,
    ncm: '', cest: '', origem: 0, observacao: '', ativo: true, codigos_barras: [], fornecedores: [],
  }
}
const form = ref(vazio())

const emQueima = computed(() => form.value.preco_queima !== null)
const sugerido = computed(() => {
  const custo = Number(form.value.custo)
  const margem = Number(form.value.margem)
  return custo > 0 && margem > 0 ? Math.round(custo * (1 + margem / 100) * 100) / 100 : null
})

// a subseção vem como "Seção › Subseção"; inativas só aparecem se forem a do produto
const opcoesSubsecao = computed(() => {
  const lista = listaSecoes.value.flatMap((s) => s.subsecoes
    .filter((sub) => (s.ativo && sub.ativo) || sub.id === form.value.subsecao_id)
    .map((sub) => ({ id: sub.id, nome: `${s.nome} › ${sub.nome}` })))
  const atual = subsecaoAtual.value
  if (atual && !lista.some((o) => o.id === atual.id)) lista.push({ id: atual.id, nome: `${atual.secao.nome} › ${atual.nome}` })
  return lista
})
const opcoesMarca = computed(() => {
  const lista = marcas.value.filter((m) => m.ativo || m.id === form.value.marca_id)
  if (marcaAtual.value && !lista.some((m) => m.id === marcaAtual.value.id)) lista.push(marcaAtual.value)
  return lista
})
const opcoesFornecedor = computed(() => {
  const lista = fornecedores.value.filter((f) => f.ativo || form.value.fornecedores.some((x) => x.fornecedor_id === f.id))
  for (const f of fornecedoresDoProduto.value) if (!lista.some((o) => o.id === f.id)) lista.push(f)
  return lista
})

function alternarQueima(sim) {
  form.value.preco_queima = sim ? '' : null
}

function acrescentarCodigo() {
  const c = soDigitos(novoCodigo.value)
  if (!c) return
  if (c.length < 8) {
    $q.notify({ type: 'warning', message: 'Código de barras tem de 8 a 14 dígitos' })
    return
  }
  if (!form.value.codigos_barras.includes(c)) form.value.codigos_barras.push(c)
  novoCodigo.value = ''
}

function preencher(produto) {
  const { id, codigo: cod, subsecao, marca, fotos: fts, criado_em, atualizado_em, fornecedores: forns, ...dados } = produto
  codigo.value = cod
  subsecaoAtual.value = subsecao
  marcaAtual.value = marca
  fotos.value = fts
  fornecedoresDoProduto.value = forns.map((f) => f.fornecedor)
  form.value = {
    ...vazio(), ...dados,
    ncm: dados.ncm ?? '', cest: dados.cest ?? '', observacao: dados.observacao ?? '',
    fornecedores: forns.map((f) => ({ fornecedor_id: f.fornecedor_id, codigo: f.codigo ?? '' })),
  }
}

async function carregar() {
  carregando.value = true
  try {
    const [s, m, f, p] = await Promise.all([
      api.get('/secoes'),
      api.get('/marcas'),
      podeEditar.value ? api.get('/fornecedores') : null,
      novo.value ? null : api.get(`/produtos/${rota.params.id}`),
    ])
    listaSecoes.value = s.data
    marcas.value = m.data
    fornecedores.value = f?.data ?? []
    if (p) preencher(p.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

onMounted(carregar)

async function salvar() {
  acrescentarCodigo()
  salvando.value = true
  try {
    const f = form.value
    const dados = {
      ...f,
      preco_queima: f.preco_queima === '' ? null : f.preco_queima,
      ncm: f.ncm || null,
      cest: f.cest || null,
      fornecedores: f.fornecedores.map((x) => ({ fornecedor_id: x.fornecedor_id, codigo: x.codigo || null })),
    }
    const resp = novo.value ? await api.post('/produtos', dados) : await api.put(`/produtos/${rota.params.id}`, dados)
    $q.notify({ type: 'positive', message: 'Produto salvo', timeout: 1500 })
    if (novo.value) await roteador.replace({ name: 'produto', params: { id: resp.data.id } })
    // a página continua montada depois do replace: mostra o que a API gravou
    preencher(resp.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}
</script>
