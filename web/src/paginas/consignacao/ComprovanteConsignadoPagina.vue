<template>
  <!-- o comprovante da transferência e da devolução (D30): o produto, o preço da transferência e a quantidade;
       o representante assina -->
  <div class="comprovante">
    <div class="sem-impressao row items-center q-gutter-sm q-pa-md">
      <q-btn flat no-caps icon="arrow_back" :label="devolucao ? 'Devoluções' : 'Transferências'" :to="{ name: 'transferencias', query: devolucao ? { aba: 'devolucoes' } : {} }" />
      <q-space />
      <q-btn unelevated no-caps color="primary" icon="print" label="Imprimir" :disable="!documento" @click="imprimir" />
    </div>

    <div v-if="erro" class="q-pa-lg text-negative">{{ erro }}</div>
    <div v-else-if="!documento" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <div v-else class="folha">
      <div class="row justify-between items-start">
        <div>
          <div class="titulo">{{ titulo }}</div>
          <div class="pequeno">{{ sessao.empresa?.nome }} · {{ formatarDataHora(documento.confirmada_em ?? documento.criado_em) }}</div>
        </div>
        <div class="pequeno text-right">
          <div>{{ documento.situacao === 'aberta' ? 'NÃO CONFIRMADA' : `Atendido por ${documento.atendida_por.nome}` }}</div>
          <div v-if="documento.autorizada_por">Liberada por {{ documento.autorizada_por.nome }}</div>
        </div>
      </div>

      <div class="bloco">
        <div class="rotulo">Representante</div>
        <div class="destaque">{{ documento.representante.codigo }} · {{ documento.representante.cliente.nome }}</div>
        <div v-if="documento.representante.cliente.cpf_cnpj">CPF {{ formatarDocumento(documento.representante.cliente.cpf_cnpj) }}</div>
      </div>

      <table class="itens">
        <thead>
          <tr>
            <th class="text-left">Produto</th>
            <th v-if="devolucao" class="text-left">Transferência</th>
            <th class="text-right">Qtd.</th>
            <th class="text-right">Preço</th>
            <th class="text-right">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="linha in linhas" :key="linha.id">
            <td>{{ formatarCodigoProduto(linha.produto.codigo) }} · {{ linha.descricao }}</td>
            <td v-if="devolucao">{{ linha.transferencia }}</td>
            <td class="text-right">{{ formatarQuantidade(linha.quantidade) }} {{ linha.produto.unidade }}</td>
            <td class="text-right">{{ formatarMoeda(linha.preco) }}</td>
            <td class="text-right">{{ formatarMoeda(linha.total) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td :colspan="devolucao ? 2 : 1">{{ linhas.length }} produto(s), {{ formatarQuantidade(pecas) }} peça(s)</td>
            <td colspan="3" class="text-right destaque">{{ formatarMoeda(documento.total) }}</td>
          </tr>
        </tfoot>
      </table>
      <div v-if="documento.observacao" class="pequeno">Observação: {{ documento.observacao }}</div>

      <div class="assinatura">
        <div v-if="devolucao">Devolvi à loja os produtos acima, que estavam comigo em consignação.</div>
        <div v-else>Recebi em consignação os produtos acima, pelos preços indicados, e me responsabilizo por eles até a devolução ou o acerto.</div>
        <div class="linha">{{ documento.representante.cliente.nome }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCodigoProduto, formatarDataHora, formatarDocumento, formatarMoeda, formatarQuantidade } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const rota = useRoute()
const sessao = useSessaoStore()
const documento = ref(null)
const erro = ref('')
// a mesma tela para os dois documentos: a rota diz qual
const devolucao = computed(() => rota.name === 'comprovante-devolucao')

const titulo = computed(() => {
  if (!devolucao.value) return `Transferência de consignado nº ${documento.value.numero}`
  return `Devolução de consignado nº ${documento.value.numero}${documento.value.retificadora ? ' (retificadora)' : ''}`
})
// a devolução guarda o item de transferência de onde a peça voltou; a transferência, o produto direto
const linhas = computed(() =>
  devolucao.value
    ? documento.value.itens.map((i) => ({
        id: i.id, produto: i.item_transferencia.produto, descricao: i.item_transferencia.descricao, quantidade: i.quantidade,
        preco: i.item_transferencia.preco, total: i.total, transferencia: i.item_transferencia.transferencia.numero,
      }))
    : documento.value.itens,
)
const pecas = computed(() => linhas.value.reduce((soma, i) => soma + Number(i.quantidade), 0))

function imprimir() {
  window.print()
}

onMounted(async () => {
  try {
    const recurso = devolucao.value ? 'devolucoes' : 'transferencias'
    documento.value = (await api.get(`/consignacao/${recurso}/${rota.params.id}`)).data
  } catch (e) {
    erro.value = mensagemDeErro(e)
    return
  }
  // aberto logo depois de confirmar: já chama a janela de impressão
  if (rota.query.imprimir) {
    await nextTick()
    imprimir()
  }
})
</script>

<style scoped>
.comprovante {
  max-width: 190mm;
  margin: 0 auto;
  background: #fff;
  color: #000;
  font-size: 12px;
}
.folha {
  padding: 5mm 0;
}
.titulo {
  font-size: 15px;
  font-weight: 700;
}
.destaque {
  font-size: 14px;
  font-weight: 700;
}
.pequeno {
  font-size: 10px;
}
.rotulo {
  font-size: 9px;
  text-transform: uppercase;
  color: #555;
}
.bloco {
  margin: 3mm 0;
}
.itens {
  width: 100%;
  border-collapse: collapse;
  margin: 2mm 0;
}
.itens th,
.itens td {
  border-bottom: 1px solid #ddd;
  padding: 1mm 0;
}
.assinatura {
  margin-top: 6mm;
}
.assinatura .linha {
  margin-top: 12mm;
  border-top: 1px solid #000;
  width: 80mm;
  font-size: 10px;
}
@media print {
  .sem-impressao {
    display: none !important;
  }
  .comprovante {
    max-width: none;
  }
}
</style>
