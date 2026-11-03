<template>
  <!-- a NFC-e da venda (D29): emite logo depois de receber, mostra a resposta da SEFAZ e imprime o DANFE na bobina -->
  <div class="nfce">
    <div class="sem-impressao q-pa-md">
      <div class="row items-center q-gutter-sm q-mb-sm">
        <q-btn flat no-caps icon="arrow_back" label="Vendas" :to="{ name: 'vendas' }" />
        <div class="piki-titulo col">NFC-e da venda</div>
      </div>

      <div v-if="trabalhando" class="row items-center q-gutter-sm q-pa-md">
        <q-spinner color="primary" size="28px" />
        <div>{{ trabalhando }}</div>
      </div>
      <q-banner v-else-if="erro" rounded class="bg-red-1 text-negative q-mb-sm">{{ erro }}</q-banner>

      <div v-if="!trabalhando && carregado" class="cartao q-pa-md">
        <div v-if="!nota" class="text-suave">A venda ainda não tem NFC-e.</div>
        <template v-else>
          <div class="row items-center q-gutter-sm">
            <q-badge :color="COR[nota.situacao]" class="text-body2">{{ NOME[nota.situacao] }}</q-badge>
            <div>NFC-e {{ nota.numero }} · série {{ nota.serie }}</div>
            <q-badge v-if="nota.ambiente === '2'" outline color="orange">Homologação</q-badge>
          </div>
          <div v-if="nota.motivo_retorno && nota.situacao !== 'autorizada'" class="q-mt-sm">
            <span v-if="nota.codigo_retorno">{{ nota.codigo_retorno }} - </span>{{ nota.motivo_retorno }}
          </div>
          <div v-if="nota.situacao === 'rejeitada'" class="text-caption text-suave q-mt-xs">
            Corrija o que a SEFAZ apontou (o NCM do produto, o cadastro da loja...) e transmita de novo: vai com o mesmo número.
          </div>
          <div v-if="nota.situacao === 'pendente'" class="text-caption text-suave q-mt-xs">
            A SEFAZ não respondeu. Consulte, ou transmita de novo: se ela já tinha autorizado, a nota vem autorizada.
          </div>
        </template>
        <div class="row q-gutter-sm q-mt-md">
          <q-btn v-if="podeTransmitir" unelevated no-caps color="primary" icon="send" :label="nota && nota.situacao !== 'inutilizada' ? 'Transmitir de novo' : 'Emitir a NFC-e'" @click="emitir" />
          <q-btn v-if="nota?.situacao === 'pendente'" flat no-caps color="primary" icon="travel_explore" label="Consultar na SEFAZ" @click="consultar" />
          <q-btn v-if="danfe" unelevated no-caps color="primary" icon="print" label="Imprimir" @click="imprimir" />
          <q-btn v-if="depois" flat no-caps color="primary" icon="arrow_forward" :label="depois.rotulo" :to="depois.rota" />
        </div>
      </div>
    </div>

    <!-- DANFE NFC-e, para a bobina de 80 mm -->
    <div v-if="danfe" class="danfe">
      <div class="centro negrito">{{ danfe.emitente.razao_social }}</div>
      <div class="centro">CNPJ {{ formatarCnpj(danfe.emitente.cnpj) }} · IE {{ danfe.emitente.inscricao_estadual }}</div>
      <div class="centro">{{ danfe.emitente.endereco }}</div>
      <div class="centro separador">Documento Auxiliar da Nota Fiscal de Consumidor Eletrônica</div>
      <div v-if="danfe.ambiente === '2'" class="centro negrito separador">EMITIDA EM AMBIENTE DE HOMOLOGAÇÃO - SEM VALOR FISCAL</div>

      <table class="itens">
        <thead>
          <tr><th class="esquerda">Código · Descrição</th><th>Qtd</th><th>Un</th><th>Vl unit</th><th>Vl total</th></tr>
        </thead>
        <tbody>
          <template v-for="item in danfe.itens" :key="item.codigo + item.descricao">
            <tr><td colspan="5" class="esquerda">{{ item.codigo }} {{ item.descricao }}</td></tr>
            <tr>
              <td></td>
              <td>{{ formatarQuantidade(item.quantidade) }}</td>
              <td>{{ item.unidade }}</td>
              <td>{{ numero(item.preco) }}</td>
              <td>{{ numero(item.total) }}</td>
            </tr>
          </template>
        </tbody>
      </table>

      <div class="linha separador"><span>Qtde. total de itens</span><span>{{ danfe.itens.length }}</span></div>
      <div class="linha"><span>Valor total R$</span><span>{{ numero(danfe.produtos) }}</span></div>
      <div v-if="Number(danfe.descontos)" class="linha"><span>Descontos R$</span><span>{{ numero(danfe.descontos) }}</span></div>
      <div v-if="Number(danfe.outros)" class="linha"><span>Acréscimos (entrega) R$</span><span>{{ numero(danfe.outros) }}</span></div>
      <div class="linha negrito"><span>Valor a pagar R$</span><span>{{ numero(danfe.total) }}</span></div>
      <div class="linha separador"><span>Forma de pagamento</span><span>Valor pago R$</span></div>
      <div v-for="(p, i) in danfe.pagamentos" :key="i" class="linha">
        <span>{{ nomePagamento(p) }}</span><span>{{ numero(p.valor) }}</span>
      </div>
      <div v-if="Number(danfe.troco)" class="linha"><span>Troco R$</span><span>{{ numero(danfe.troco) }}</span></div>

      <div class="centro separador negrito">Consulte pela chave de acesso em</div>
      <div class="centro">{{ danfe.url_consulta }}</div>
      <div class="centro chave">{{ chaveFormatada }}</div>

      <div class="centro separador">
        {{ danfe.consumidor ? `CONSUMIDOR ${formatarDocumento(danfe.consumidor.documento)}` : 'CONSUMIDOR NÃO IDENTIFICADO' }}
      </div>
      <div class="centro separador negrito">NFC-e nº {{ danfe.numero }} · Série {{ danfe.serie }} · {{ formatarDataHora(danfe.emissao) }}</div>
      <div v-if="danfe.protocolo" class="centro">Protocolo de autorização: {{ danfe.protocolo }}</div>
      <div v-if="danfe.autorizada_em" class="centro">Data de autorização: {{ formatarDataHora(danfe.autorizada_em) }}</div>
      <div v-if="danfe.situacao === 'cancelada'" class="centro negrito separador">NOTA CANCELADA</div>
      <!-- o SVG vem da própria API, gerado do texto do QR Code -->
      <div v-if="danfe.qrcode_svg" class="qrcode" v-html="danfe.qrcode_svg" />
      <div v-if="danfe.informacoes" class="centro">{{ danfe.informacoes }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCnpj, formatarDataHora, formatarDocumento, formatarQuantidade } from '@/servicos/formatos'

const NOME = { pendente: 'Pendente', rejeitada: 'Rejeitada', autorizada: 'Autorizada', cancelada: 'Cancelada', denegada: 'Denegada', inutilizada: 'Inutilizada' }
const COR = { pendente: 'orange', rejeitada: 'negative', autorizada: 'positive', cancelada: 'grey', denegada: 'negative', inutilizada: 'grey' }
const PAGAMENTOS = {
  '01': 'Dinheiro', '03': 'Cartão de crédito', '04': 'Cartão de débito', '05': 'Crédito loja', '16': 'Depósito bancário',
  '17': 'PIX', '90': 'Sem pagamento',
}
// depois da nota, o que mais sai na impressora (o carnê, o canhoto da entrega)
const PROXIMOS = { carne: 'Imprimir o carnê', 'canhoto-entrega': 'Imprimir o canhoto da entrega' }

const rota = useRoute()
const nota = ref(null)
const danfe = ref(null)
const carregado = ref(false)
const trabalhando = ref('')
const erro = ref('')

const podeTransmitir = computed(() => !nota.value || ['pendente', 'rejeitada', 'inutilizada'].includes(nota.value.situacao))
const depois = computed(() => {
  const nome = rota.query.depois
  return PROXIMOS[nome] ? { rotulo: PROXIMOS[nome], rota: { name: nome, params: { id: rota.params.id }, query: { imprimir: 1 } } } : null
})
const chaveFormatada = computed(() => danfe.value?.chave.match(/.{1,4}/g).join(' '))

function numero(valor) {
  return Number(valor).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function nomePagamento(p) {
  return PAGAMENTOS[p.tipo] ?? p.descricao ?? 'Outros'
}

async function mostrar(dados, imprimirLogo = false) {
  nota.value = dados
  danfe.value = null
  if (!dados || !['autorizada', 'cancelada'].includes(dados.situacao)) return
  danfe.value = (await api.get(`/notas/${dados.id}/danfe`)).data
  if (imprimirLogo) {
    await nextTick()
    imprimir()
  }
}

async function trabalhar(mensagem, acao) {
  trabalhando.value = mensagem
  erro.value = ''
  try {
    await acao()
  } catch (e) {
    erro.value = mensagemDeErro(e)
    // a SEFAZ não respondeu: a nota ficou pendente
    await mostrar((await api.get(`/vendas/${rota.params.id}/nfce`)).data).catch(() => {})
  } finally {
    trabalhando.value = ''
    carregado.value = true
  }
}

function emitir() {
  return trabalhar('Transmitindo para a SEFAZ...', async () => {
    await mostrar((await api.post(`/vendas/${rota.params.id}/nfce`)).data, true)
  })
}

function consultar() {
  return trabalhar('Consultando na SEFAZ...', async () => {
    await mostrar((await api.post(`/notas/${nota.value.id}/consultar`)).data, true)
  })
}

function imprimir() {
  window.print()
}

onMounted(async () => {
  await trabalhar('Carregando...', async () => {
    const atual = (await api.get(`/vendas/${rota.params.id}/nfce`)).data
    if (!atual && rota.query.emitir) {
      trabalhando.value = 'Transmitindo para a SEFAZ...'
      await mostrar((await api.post(`/vendas/${rota.params.id}/nfce`)).data, true)
    } else await mostrar(atual)
  })
})
</script>

<style scoped>
.nfce {
  max-width: 640px;
  margin: 0 auto;
}
.danfe {
  width: 72mm;
  margin: 0 auto 16px;
  background: #fff;
  color: #000;
  font-family: 'Courier New', monospace;
  font-size: 10px;
  line-height: 1.3;
  padding: 2mm 0;
}
.centro {
  text-align: center;
}
.negrito {
  font-weight: 700;
}
.separador {
  border-top: 1px dashed #000;
  margin-top: 2mm;
  padding-top: 1mm;
}
.linha {
  display: flex;
  justify-content: space-between;
}
.chave {
  font-size: 9px;
  word-break: break-all;
}
.itens {
  width: 100%;
  border-collapse: collapse;
  margin-top: 2mm;
}
.itens th,
.itens td {
  text-align: right;
  padding: 0;
  font-weight: 400;
}
.itens .esquerda {
  text-align: left;
}
.qrcode {
  width: 30mm;
  margin: 2mm auto;
}
.qrcode :deep(svg) {
  width: 100%;
  height: auto;
}
@media print {
  @page {
    size: 80mm auto;
    margin: 0;
  }
  .sem-impressao {
    display: none !important;
  }
  .nfce {
    max-width: none;
  }
  .danfe {
    margin: 0 auto;
  }
}
</style>
