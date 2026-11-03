<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'vendas' }" />
      <div class="piki-titulo col">{{ venda ? `Venda ${venda.numero}` : 'Venda' }}</div>
      <template v-if="venda">
        <q-badge :color="CORES[venda.situacao]" class="q-mr-md">{{ SITUACOES[venda.situacao] }}</q-badge>
        <q-btn v-if="(aberta || fechada) && podeVender" flat no-caps color="negative" icon="close" label="Cancelar venda" @click="cancelar" />
        <q-btn v-if="fechada && (podeVender || podeReceber)" flat no-caps icon="lock_open" label="Reabrir" class="q-ml-sm" @click="reabrir" />
        <q-btn v-if="aberta && podeVender" unelevated no-caps color="primary" icon="done_all" label="Fechar venda" class="q-ml-sm" :loading="fechando" @click="fechar" />
        <q-btn v-if="fechada && podeReceber" unelevated no-caps color="primary" icon="point_of_sale" label="Receber" class="q-ml-sm" :to="{ name: 'receber-venda', params: { id: venda.id } }" />
      </template>
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <div v-else-if="venda" class="row q-col-gutter-md">
      <div class="col-12 col-md-8">
        <section v-if="editavel" class="cartao q-pa-md q-mb-md">
          <form class="row q-col-gutter-sm items-start" @submit.prevent="procurar">
            <q-input
              ref="campoBusca"
              v-model="termo"
              outlined
              autofocus
              label="Código, código de barras ou nome do produto"
              :loading="procurando"
              class="col"
            >
              <template #prepend><q-icon name="qr_code_scanner" /></template>
            </q-input>
            <q-input v-model="quantidade" outlined type="number" step="any" min="0" label="Qtd." class="col-3 col-sm-2" />
            <div class="col-auto"><q-btn type="submit" unelevated no-caps color="primary" icon="add" label="Incluir" class="q-py-sm" /></div>
          </form>
          <q-list v-if="resultados.length" bordered separator class="q-mt-sm rounded-borders">
            <q-item v-for="p in resultados" :key="p.id" v-ripple clickable @click="incluir(p)">
              <q-item-section>
                <q-item-label>{{ p.nome }} <q-badge v-if="Number(p.preco_queima)" color="deep-orange" label="Queima" /></q-item-label>
                <q-item-label caption>{{ formatarCodigoProduto(p.codigo) }}<template v-if="p.estoque !== null && p.estoque !== undefined"> · estoque {{ formatarQuantidade(p.estoque) }}</template></q-item-label>
              </q-item-section>
              <q-item-section side>{{ formatarMoeda(p.preco_queima || p.preco_venda) }}</q-item-section>
            </q-item>
          </q-list>
        </section>

        <q-table
          flat
          bordered
          :rows="venda.itens"
          :columns="colunas"
          row-key="id"
          :pagination="{ rowsPerPage: 0 }"
          hide-pagination
          no-data-label="Nenhum item ainda"
        >
          <template #body-cell-descricao="props">
            <q-td :props="props">
              <div>{{ props.row.descricao }} <q-badge v-if="props.row.em_queima" color="deep-orange" label="Queima" /></div>
              <div class="text-caption text-suave">{{ formatarCodigoProduto(props.row.produto.codigo) }}</div>
              <div v-if="falta(props.row)" class="text-caption text-negative">
                <q-icon name="warning" /> Estoque da loja: {{ formatarQuantidade(props.row.disponivel) }}
              </div>
            </q-td>
          </template>
          <template #body-cell-acoes="props">
            <q-td :props="props" auto-width>
              <template v-if="editavel">
                <q-btn flat round dense size="sm" icon="edit" aria-label="Alterar" @click="abrirItem(props.row)" />
                <q-btn flat round dense size="sm" icon="delete" aria-label="Tirar" @click="excluir(props.row)" />
              </template>
            </q-td>
          </template>
        </q-table>
      </div>

      <div class="col-12 col-md-4">
        <section class="cartao q-pa-md q-mb-md q-gutter-y-sm">
          <q-select
            v-model="cabecalho.cliente_id"
            outlined
            use-input
            input-debounce="300"
            clearable
            label="Cliente cadastrado"
            :options="clientes"
            option-value="id"
            option-label="nome"
            emit-value
            map-options
            :readonly="!editavel"
            @filter="buscarClientes"
            @update:model-value="salvarCabecalho"
          >
            <template #no-option><q-item><q-item-section class="text-suave">Digite parte do nome ou o CPF</q-item-section></q-item></template>
          </q-select>
          <template v-if="!cabecalho.cliente_id">
            <q-input
              v-model="cabecalho.consumidor.nome"
              outlined
              label="Nome de quem está comprando *"
              hint="Sem cadastro (venda a consumidor): pode ser só o primeiro nome; o caixa chama por ele"
              maxlength="60"
              :readonly="!editavel"
              @change="salvarCabecalho"
            />
            <q-expansion-item v-model="maisDados" dense dense-toggle switch-toggle-side label="Mais dados do consumidor (opcional)" class="text-caption">
              <div class="q-gutter-y-sm q-pt-sm">
                <q-input
                  v-model="cabecalho.consumidor.cpf"
                  outlined
                  dense
                  label="CPF"
                  mask="###.###.###-##"
                  unmasked-value
                  :readonly="!editavel"
                  @change="aoMudarCpf"
                />
                <div class="row q-col-gutter-sm">
                  <q-input
                    v-model="cabecalho.consumidor.aniversario"
                    outlined
                    dense
                    label="Aniversário (dia/mês)"
                    mask="##/##"
                    class="col-6"
                    :readonly="!editavel"
                    @change="salvarCabecalho"
                  />
                  <q-input
                    v-model="cabecalho.consumidor.telefone"
                    outlined
                    dense
                    label="Telefone"
                    :mask="mascaraTelefone(cabecalho.consumidor.telefone)"
                    unmasked-value
                    class="col-6"
                    :readonly="!editavel"
                    @change="salvarCabecalho"
                  />
                </div>
                <q-input v-model="cabecalho.consumidor.email" outlined dense type="email" label="E-mail" maxlength="100" :readonly="!editavel" @change="salvarCabecalho" />
              </div>
            </q-expansion-item>
          </template>
          <q-select
            v-model="cabecalho.forma_pagamento_id"
            outlined
            label="Forma de pagamento"
            :options="formas"
            option-value="id"
            :option-label="(f) => (Number(f.desconto) ? `${f.nome} (${formatarPercentual(f.desconto)} de desconto)` : f.nome)"
            emit-value
            map-options
            :readonly="!editavel"
            @update:model-value="trocarForma"
          />
          <q-select
            v-if="forma && forma.parcelas > 1"
            v-model="cabecalho.parcelas"
            outlined
            label="Parcelas"
            :options="parcelas"
            emit-value
            map-options
            :readonly="!editavel"
            @update:model-value="salvarCabecalho"
          />
          <q-input v-model="cabecalho.observacao" outlined label="Observação" maxlength="200" :readonly="!editavel" @change="salvarCabecalho" />
          <q-toggle v-model="cabecalho.comEntrega" label="Com entrega" :disable="!editavel" @update:model-value="trocarEntrega" />
          <div v-if="cabecalho.comEntrega" class="q-gutter-y-sm">
            <q-input v-model="entrega.taxa" outlined dense type="number" step="0.01" min="0" prefix="R$" label="Taxa de entrega" :readonly="!editavel" @change="salvarCabecalho" />
            <campo-cep v-model="entrega.cep" dense label="CEP" :buscando="buscandoCep" :readonly="!editavel" @buscar="buscarEnderecoDoCep" />
            <q-input v-model="entrega.logradouro" outlined dense label="Rua *" maxlength="100" :readonly="!editavel" @change="salvarCabecalho" />
            <div class="row q-col-gutter-sm">
              <q-input v-model="entrega.numero" outlined dense label="Número *" maxlength="20" class="col-4" :readonly="!editavel" @change="salvarCabecalho" />
              <q-input v-model="entrega.complemento" outlined dense label="Complemento" maxlength="60" class="col-8" :readonly="!editavel" @change="salvarCabecalho" />
            </div>
            <q-input v-model="entrega.bairro" outlined dense label="Bairro *" maxlength="60" :readonly="!editavel" @change="salvarCabecalho" />
            <selecao-cidade v-model="entrega.cidade_id" v-model:cidade="cidadeEntrega" dense label="Cidade *" :readonly="!editavel" @update:model-value="salvarCabecalho" />
            <q-input v-model="entrega.ponto_referencia" outlined dense label="Ponto de referência" maxlength="60" :readonly="!editavel" @change="salvarCabecalho" />
            <q-input
              v-model="entrega.telefone"
              outlined
              dense
              label="Telefone de quem recebe"
              :mask="mascaraTelefone(entrega.telefone)"
              unmasked-value
              :readonly="!editavel"
              @change="salvarCabecalho"
            />
          </div>
          <div v-if="aberta && forma?.tipo === 'crediario' && !venda.cliente" class="text-caption text-negative">O crediário pede o cliente cadastrado.</div>
          <div v-if="venda.credito" class="credito q-pa-sm rounded-borders text-caption">
            <div v-if="venda.credito.impedimento" class="text-negative"><q-icon name="block" /> {{ venda.credito.impedimento }}</div>
            <template v-else>
              <div class="row justify-between"><span>Limite do cliente</span><span>{{ formatarMoeda(venda.credito.limite) }}</span></div>
              <div class="row justify-between"><span>Em aberto (todas as lojas)</span><span>{{ formatarMoeda(venda.credito.em_aberto) }}</span></div>
              <div v-if="Number(venda.credito.em_prejuizo)" class="row justify-between text-negative">
                <span>· dos quais no prejuízo</span><span>{{ formatarMoeda(venda.credito.em_prejuizo) }}</span>
              </div>
              <div class="row justify-between text-weight-bold" :class="{ 'text-negative': passaDoLimite }">
                <span>Disponível</span><span>{{ formatarMoeda(venda.credito.disponivel) }}</span>
              </div>
              <div v-if="passaDoLimite" class="text-negative q-mt-xs">Passa do disponível: o caixa vai pedir uma entrada ou a autorização da gerência.</div>
            </template>
          </div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="row justify-between"><span>Subtotal</span><span>{{ formatarMoeda(venda.subtotal) }}</span></div>
          <div class="row justify-between items-center">
            <span>
              Desconto <span v-if="Number(venda.desconto)" class="text-caption text-suave">({{ formatarPercentual(percentual) }})</span>
              <q-btn v-if="editavel && venda.itens.length" flat dense no-caps size="sm" color="primary" label="Dar desconto" @click="abrirDesconto" />
            </span>
            <span>{{ formatarMoeda(-venda.desconto) }}</span>
          </div>
          <div v-if="venda.entrega" class="row justify-between"><span>Entrega</span><span>{{ formatarMoeda(venda.taxa_entrega) }}</span></div>
          <q-separator class="q-my-sm" />
          <div class="row justify-between text-h6"><span>Total</span><span>{{ formatarMoeda(venda.total) }}</span></div>
          <div v-if="venda.parcelas > 1" class="text-right text-caption text-suave">
            {{ venda.parcelas }}x de {{ formatarMoeda(venda.total / venda.parcelas) }}
          </div>
          <div v-if="venda.desconto_autorizado_por" class="text-caption text-suave q-mt-sm">Desconto autorizado por {{ venda.desconto_autorizado_por.nome }}</div>
          <div v-if="venda.parcelas_autorizadas_por" class="text-caption text-suave">Parcelas autorizadas por {{ venda.parcelas_autorizadas_por.nome }}</div>
          <div v-if="venda.limite_autorizado_por" class="text-caption text-suave">Crediário acima do limite autorizado por {{ venda.limite_autorizado_por.nome }}</div>
        </section>

        <section v-if="venda.carne" class="cartao q-pa-md q-mb-md">
          <div class="row items-center q-mb-sm">
            <div class="col text-weight-medium">Carnê {{ venda.carne.id }}</div>
            <q-btn flat dense no-caps color="primary" icon="print" label="Imprimir carnê" :to="{ name: 'carne', params: { id: venda.id } }" />
          </div>
          <div class="text-caption text-suave">A prazo {{ formatarMoeda(venda.a_prazo) }}, contado de {{ formatarDataHora(venda.data_base) }}</div>
          <div v-for="p in venda.carne.parcelas" :key="p.numero" class="row justify-between text-caption">
            <span>{{ p.numero }}/{{ venda.carne.parcelas.length }} · vence {{ formatarDataHora(p.vencimento) }}</span>
            <span>{{ formatarMoeda(p.valor) }}</span>
          </div>
        </section>

        <section class="cartao q-pa-md text-caption">
          <div>Vendedor: {{ venda.vendedor.nome }} · {{ formatarDataHora(venda.criado_em) }}</div>
          <div v-if="fechada">Fechada em {{ formatarDataHora(venda.fechada_em) }}: esperando o caixa</div>
          <div v-if="aberta || fechada">Vence em {{ formatarDataHora(venda.vence_em).slice(0, 10) }}</div>
          <template v-if="venda.situacao === 'recebida'">
            <div>Recebida por {{ venda.recebida_por?.nome }} no {{ venda.sessao_caixa?.caixa.nome }} · {{ formatarDataHora(venda.recebida_em) }}</div>
            <div v-for="(pg, i) in venda.pagamentos" :key="i">
              {{ pg.forma_pagamento.nome }}<template v-if="pg.parcelas > 1"> em {{ pg.parcelas }}x</template>: {{ formatarMoeda(pg.valor) }}
            </div>
            <div v-if="venda.troco !== null">Recebido {{ formatarMoeda(venda.valor_recebido) }} · troco {{ formatarMoeda(venda.troco) }}</div>
          </template>
          <div v-if="venda.situacao === 'cancelada'">
            Cancelada por {{ venda.cancelada_por?.nome }} · {{ formatarDataHora(venda.cancelada_em) }}: {{ venda.motivo_cancelamento }}
          </div>
        </section>
      </div>
    </div>

    <!-- alterar item -->
    <q-dialog v-model="item.aberto">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="salvarItem">
          <q-card-section class="piki-titulo">{{ item.descricao }}</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-input v-model="item.quantidade" outlined autofocus type="number" step="any" min="0" label="Quantidade *" />
            <q-input
              v-model="item.desconto"
              outlined
              type="number"
              step="0.01"
              min="0"
              prefix="R$"
              label="Desconto no item"
              :disable="item.em_queima"
              :hint="item.em_queima ? 'Produto em queima: não tem desconto' : ''"
            />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Salvar" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- desconto no total -->
    <q-dialog v-model="desconto.aberto">
      <q-card class="cartao-estreito">
        <q-form @submit.prevent="darDesconto">
          <q-card-section class="piki-titulo">Desconto na venda</q-card-section>
          <q-card-section class="q-gutter-sm q-pt-none">
            <q-btn-toggle v-model="desconto.em" no-caps unelevated toggle-color="primary" :options="[{ label: '%', value: 'percentual' }, { label: 'R$', value: 'valor' }]" />
            <q-input v-model="desconto.valor" outlined autofocus type="number" step="0.01" min="0" :label="desconto.em === 'valor' ? 'Desconto em reais' : 'Desconto em %'" />
            <div class="text-caption text-suave">Vale para a venda toda e é dividido entre os itens, na proporção do valor de cada um.</div>
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" />
            <q-btn type="submit" color="primary" unelevated no-caps label="Aplicar" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <dialogo-autorizacao :estado="autorizacao" @responder="responderAutorizacao" />
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import CampoCep from '@/componentes/CampoCep.vue'
import DialogoAutorizacao from '@/componentes/DialogoAutorizacao.vue'
import SelecaoCidade from '@/componentes/SelecaoCidade.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { usarAutorizacao } from '@/servicos/autorizacao'
import { usarCep } from '@/servicos/cep'
import { formatarCodigoProduto, formatarDataHora, formatarMoeda, formatarQuantidade, mascaraTelefone } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const SITUACOES = { aberta: 'Aberta', fechada: 'Fechada', recebida: 'Recebida', cancelada: 'Cancelada', vencida: 'Vencida' }
const CORES = { aberta: 'warning', fechada: 'primary', recebida: 'positive', cancelada: 'grey', vencida: 'grey-7' }
const SEM_CONSUMIDOR = { nome: '', cpf: '', aniversario: '', telefone: '', email: '' }
const SEM_ENTREGA = { taxa: '', cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade_id: null, ponto_referencia: '', telefone: '' }

const $q = useQuasar()
const rota = useRoute()
const sessao = useSessaoStore()

const venda = ref(null)
const carregando = ref(true)
const formas = ref([])
const clientes = ref([])
const cabecalho = ref({ cliente_id: null, forma_pagamento_id: null, parcelas: 1, observacao: '', consumidor: { ...SEM_CONSUMIDOR }, comEntrega: false })
const entrega = ref({ ...SEM_ENTREGA })
const cidadeEntrega = ref(null) // { id, nome, uf }, para o campo mostrar o nome
const maisDados = ref(false)
const fechando = ref(false)
const campoBusca = ref(null)
const termo = ref('')
const quantidade = ref('1')
const procurando = ref(false)
const resultados = ref([])
const item = ref({ aberto: false })
const desconto = ref({ aberto: false, em: 'percentual', valor: '' })
const { autorizacao, responder: responderAutorizacao, comAutorizacao } = usarAutorizacao()

const podeVender = computed(() => sessao.pode('vendas.vender'))
const podeReceber = computed(() => sessao.pode('caixa.operar'))
const aberta = computed(() => venda.value?.situacao === 'aberta')
const fechada = computed(() => venda.value?.situacao === 'fechada')
const editavel = computed(() => aberta.value && podeVender.value)
const url = computed(() => `/vendas/${rota.params.id}`)
const forma = computed(() => formas.value.find((f) => f.id === venda.value?.forma_pagamento?.id) ?? null)
const parcelas = computed(() =>
  Array.from({ length: forma.value?.parcelas ?? 1 }, (_, i) => ({
    value: i + 1,
    label: i + 1 > forma.value.parcelas_sem_autorizacao ? `${i + 1}x (pede autorização)` : `${i + 1}x`,
  })),
)
const percentual = computed(() => (Number(venda.value?.subtotal) ? (Number(venda.value.desconto) * 100) / Number(venda.value.subtotal) : 0))
const passaDoLimite = computed(() => !!venda.value?.credito && Number(venda.value.credito.disponivel) < Number(venda.value.total))

const colunas = [
  { name: 'descricao', label: 'Produto', field: 'descricao', align: 'left' },
  { name: 'quantidade', label: 'Qtd.', field: 'quantidade', align: 'right', format: formatarQuantidade },
  { name: 'preco', label: 'Preço', field: 'preco', align: 'right', format: formatarMoeda },
  { name: 'desconto', label: 'Desconto', field: 'desconto', align: 'right', format: (v) => (Number(v) ? formatarMoeda(-v) : '') },
  { name: 'total', label: 'Total', field: 'total', align: 'right', format: formatarMoeda },
  { name: 'acoes', label: '', field: 'id' },
]

function formatarPercentual(valor) {
  return `${Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%`
}

function falta(linha) {
  return aberta.value && linha.disponivel !== null && Number(linha.disponivel) < Number(linha.quantidade)
}

function mostrar(dados) {
  venda.value = dados
  const c = dados.consumidor
  cabecalho.value = {
    cliente_id: dados.cliente?.id ?? null,
    forma_pagamento_id: dados.forma_pagamento?.id ?? null,
    parcelas: dados.parcelas,
    observacao: dados.observacao ?? '',
    consumidor: {
      nome: dados.cliente ? '' : (dados.comprador ?? ''),
      cpf: c?.cpf ?? '',
      aniversario: c?.dia_nascimento ? `${String(c.dia_nascimento).padStart(2, '0')}/${String(c.mes_nascimento).padStart(2, '0')}` : '',
      telefone: c?.telefone ?? '',
      email: c?.email ?? '',
    },
    comEntrega: !!dados.entrega,
  }
  const e = dados.entrega
  entrega.value = e
    ? { ...SEM_ENTREGA, ...Object.fromEntries(Object.entries(e).map(([k, v]) => [k, v ?? ''])), cidade_id: e.cidade?.id ?? null, taxa: String(Number(e.taxa)) }
    : { ...SEM_ENTREGA }
  delete entrega.value.cidade
  cidadeEntrega.value = e?.cidade ?? null
  if (dados.cliente && !clientes.value.some((c) => c.id === dados.cliente.id)) clientes.value = [dados.cliente, ...clientes.value]
}

/** Manda o pedido; se passar do limite, pede a autorização e manda de novo com ela. Devolve a venda, ou null. */
async function enviar(pedido) {
  try {
    const data = await comAutorizacao(pedido)
    if (data) mostrar(data)
    else if (venda.value) mostrar(venda.value) // desistiu: desfaz o que mudou na tela
    return data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    if (venda.value) mostrar(venda.value)
    return null
  }
}

async function procurar() {
  const texto = termo.value.trim()
  if (!texto) return
  procurando.value = true
  try {
    const { data } = await api.get('/produtos', { params: { busca: texto, limite: 20 } })
    if (data.itens.length === 1) await incluir(data.itens[0])
    else if (!data.itens.length) $q.notify({ type: 'warning', message: 'Nenhum produto encontrado' })
    else resultados.value = data.itens
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    procurando.value = false
  }
}

async function incluir(produto) {
  const ok = await enviar((autorizacao) =>
    api.post(`${url.value}/itens`, { produto_id: produto.id, quantidade: String(quantidade.value || 1), autorizacao }),
  )
  if (ok) {
    termo.value = ''
    quantidade.value = '1'
    resultados.value = []
    campoBusca.value?.focus()
  }
}

function abrirItem(linha) {
  item.value = {
    aberto: true,
    id: linha.id,
    descricao: linha.descricao,
    em_queima: linha.em_queima,
    quantidade: String(Number(linha.quantidade)),
    desconto: String(Number(linha.desconto)),
  }
}

async function salvarItem() {
  const { id, quantidade: qtd, desconto: valor } = item.value
  const ok = await enviar((autorizacao) => api.put(`${url.value}/itens/${id}`, { quantidade: String(qtd), desconto: String(valor || 0), autorizacao }))
  if (ok) item.value.aberto = false
}

function excluir(linha) {
  $q.dialog({
    title: 'Tirar item',
    message: `Tirar ${linha.descricao} da venda?`,
    cancel: { flat: true, label: 'Não' },
    ok: { label: 'Tirar', color: 'negative' },
  }).onOk(() => enviar(() => api.delete(`${url.value}/itens/${linha.id}`)))
}

function abrirDesconto() {
  desconto.value = { aberto: true, em: 'percentual', valor: '' }
}

async function darDesconto() {
  const { em, valor } = desconto.value
  const ok = await enviar((autorizacao) => api.post(`${url.value}/desconto`, { [em]: String(valor || 0), autorizacao }))
  if (ok) desconto.value.aberto = false
}

function dadosDoConsumidor() {
  const { nome, cpf, aniversario, telefone, email } = cabecalho.value.consumidor
  const [dia, mes] = /^\d{2}\/\d{2}$/.test(aniversario ?? '') ? aniversario.split('/').map(Number) : [null, null]
  return { nome: nome || null, cpf: cpf || null, dia_nascimento: dia, mes_nascimento: mes, telefone: telefone || null, email: email || null }
}

function dadosDaEntrega() {
  if (!cabecalho.value.comEntrega) return null
  const e = entrega.value
  return { ...e, taxa: String(Number(e.taxa) || 0) }
}

function salvarCabecalho() {
  const { cliente_id, forma_pagamento_id, parcelas: n, observacao } = cabecalho.value
  const consumidor = cliente_id ? null : dadosDoConsumidor()
  return enviar((autorizacao) =>
    api.put(url.value, { cliente_id, forma_pagamento_id, parcelas: n, observacao, consumidor, entrega: dadosDaEntrega(), autorizacao }),
  )
}

/** CPF completo: traz o que já se sabe de quem tem esse CPF (cliente cadastrado ou consumidor de outra compra). */
async function aoMudarCpf() {
  const cpf = cabecalho.value.consumidor.cpf
  if (cpf?.length === 11) {
    try {
      const { data } = await api.get(`/consumidores/${cpf}`)
      if (data.cliente) {
        clientes.value = [data.cliente, ...clientes.value.filter((c) => c.id !== data.cliente.id)]
        cabecalho.value.cliente_id = data.cliente.id
        $q.notify({ type: 'info', message: `Este CPF é do cliente cadastrado ${data.cliente.nome}` })
      } else if (data.consumidor) {
        const c = data.consumidor
        const atual = cabecalho.value.consumidor
        cabecalho.value.consumidor = {
          nome: atual.nome || c.nome,
          cpf,
          aniversario: atual.aniversario || (c.dia_nascimento ? `${String(c.dia_nascimento).padStart(2, '0')}/${String(c.mes_nascimento).padStart(2, '0')}` : ''),
          telefone: atual.telefone || c.telefone || '',
          email: atual.email || c.email || '',
        }
      }
    } catch (e) {
      $q.notify({ type: 'warning', message: mensagemDeErro(e) })
      return
    }
  }
  salvarCabecalho()
}

/** Ao ligar a entrega com cliente cadastrado, o endereço dele já vem preenchido. */
function trocarEntrega(ligada) {
  const cliente = venda.value?.cliente
  if (ligada && cliente && !entrega.value.logradouro) {
    entrega.value = {
      ...entrega.value,
      cep: cliente.cep ?? '',
      logradouro: cliente.logradouro ?? '',
      numero: cliente.numero ?? '',
      complemento: cliente.complemento ?? '',
      bairro: cliente.setor?.nome ?? '',
      cidade_id: cliente.setor?.cidade?.id ?? null,
      ponto_referencia: cliente.ponto_referencia ?? '',
      telefone: cliente.telefones?.[0]?.numero ?? '',
    }
    cidadeEntrega.value = cliente.setor?.cidade ?? null
  }
  salvarCabecalho()
}

const { buscando: buscandoCep, buscar: buscarCep } = usarCep(entrega, { cep: 'cep', rua: 'logradouro', bairro: 'bairro', cidade: 'cidade_id' }, { cidade: cidadeEntrega, limiteRua: 100 })

async function buscarEnderecoDoCep() {
  await buscarCep()
  salvarCabecalho()
}

async function fechar() {
  fechando.value = true
  const data = await enviar(() => api.post(`${url.value}/fechar`))
  fechando.value = false
  if (data) $q.notify({ type: 'positive', message: `Venda fechada: ${data.comprador} já pode ir ao caixa` })
}

function reabrir() {
  $q.dialog({
    title: 'Reabrir venda',
    message: 'A venda volta para o vendedor mudar e sai da fila do caixa.',
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Reabrir' },
  }).onOk(() => enviar(() => api.post(`${url.value}/reabrir`)))
}

function trocarForma() {
  cabecalho.value.parcelas = 1
  salvarCabecalho()
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

function cancelar() {
  $q.dialog({
    title: 'Cancelar venda',
    message: 'Por que a venda está sendo cancelada?',
    prompt: { model: '', type: 'text', outlined: true, isValid: (v) => !!v.trim() },
    cancel: { flat: true, label: 'Voltar' },
    ok: { label: 'Cancelar venda', color: 'negative' },
  }).onOk((motivo) => enviar(() => api.post(`${url.value}/cancelar`, { motivo })))
}

onMounted(async () => {
  try {
    const [v, f] = await Promise.all([api.get(url.value), api.get('/formas-pagamento', { params: { so_ativas: true } })])
    formas.value = f.data
    mostrar(v.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})
</script>

<style scoped>
.credito {
  background: rgba(127, 127, 127, 0.1);
}
</style>
