<template>
  <!-- o comprovante da transferência (D30): o produto, o preço com que sai e a quantidade; o representante assina -->
  <div class="comprovante">
    <div class="sem-impressao row items-center q-gutter-sm q-pa-md">
      <q-btn flat no-caps icon="arrow_back" label="Transferências" :to="{ name: 'transferencias' }" />
      <q-space />
      <q-btn unelevated no-caps color="primary" icon="print" label="Imprimir" :disable="!transferencia" @click="imprimir" />
    </div>

    <div v-if="erro" class="q-pa-lg text-negative">{{ erro }}</div>
    <div v-else-if="!transferencia" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <div v-else class="folha">
      <div class="row justify-between items-start">
        <div>
          <div class="titulo">Transferência de consignado nº {{ transferencia.numero }}</div>
          <div class="pequeno">{{ sessao.empresa?.nome }} · {{ formatarDataHora(transferencia.confirmada_em ?? transferencia.criado_em) }}</div>
        </div>
        <div class="pequeno text-right">
          {{ transferencia.situacao === 'aberta' ? 'NÃO CONFIRMADA' : `Atendido por ${transferencia.atendida_por.nome}` }}
        </div>
      </div>

      <div class="bloco">
        <div class="rotulo">Representante</div>
        <div class="destaque">{{ transferencia.representante.codigo }} · {{ transferencia.representante.cliente.nome }}</div>
        <div v-if="transferencia.representante.cliente.cpf_cnpj">CPF {{ formatarDocumento(transferencia.representante.cliente.cpf_cnpj) }}</div>
      </div>

      <table class="itens">
        <thead>
          <tr><th class="text-left">Produto</th><th class="text-right">Qtd.</th><th class="text-right">Preço</th><th class="text-right">Total</th></tr>
        </thead>
        <tbody>
          <tr v-for="item in transferencia.itens" :key="item.id">
            <td>{{ formatarCodigoProduto(item.produto.codigo) }} · {{ item.descricao }}</td>
            <td class="text-right">{{ formatarQuantidade(item.quantidade) }} {{ item.produto.unidade }}</td>
            <td class="text-right">{{ formatarMoeda(item.preco) }}</td>
            <td class="text-right">{{ formatarMoeda(item.total) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td>{{ transferencia.itens.length }} produto(s), {{ formatarQuantidade(pecas) }} peça(s)</td>
            <td colspan="3" class="text-right destaque">{{ formatarMoeda(transferencia.total) }}</td>
          </tr>
        </tfoot>
      </table>

      <div class="assinatura">
        <div>Recebi em consignação os produtos acima, pelos preços indicados, e me responsabilizo por eles até a devolução ou o acerto.</div>
        <div class="linha">{{ transferencia.representante.cliente.nome }}</div>
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
const transferencia = ref(null)
const erro = ref('')

const pecas = computed(() => transferencia.value.itens.reduce((soma, i) => soma + Number(i.quantidade), 0))

function imprimir() {
  window.print()
}

onMounted(async () => {
  try {
    transferencia.value = (await api.get(`/consignacao/transferencias/${rota.params.id}`)).data
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
