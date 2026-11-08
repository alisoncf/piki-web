<template>
  <!-- o comprovante do pagamento de comissão ao representante (D30); ele assina -->
  <div class="comprovante">
    <div class="sem-impressao row items-center q-gutter-sm q-pa-md">
      <q-btn flat no-caps icon="arrow_back" label="Comissões" :to="{ name: 'comissoes' }" />
      <q-space />
      <q-btn unelevated no-caps color="primary" icon="print" label="Imprimir" :disable="!pagamento" @click="imprimir" />
    </div>

    <div v-if="erro" class="q-pa-lg text-negative">{{ erro }}</div>
    <div v-else-if="!pagamento" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <div v-else class="folha">
      <div class="titulo">Comprovante de pagamento de comissão nº {{ pagamento.id }}</div>
      <div class="pequeno">{{ sessao.empresa?.nome }} · {{ formatarDataHora(pagamento.data_hora) }}{{ pagamento.usuario ? ` · ${pagamento.usuario}` : '' }}</div>
      <div v-if="pagamento.estornado_em" class="destaque q-mt-sm">PAGAMENTO DESFEITO em {{ formatarDataHora(pagamento.estornado_em) }}</div>

      <div class="bloco">
        <div class="rotulo">Representante</div>
        <div class="destaque">{{ pagamento.representante.codigo }} · {{ pagamento.representante.cliente.nome }}</div>
      </div>
      <div class="bloco destaque">{{ formatarMoeda(pagamento.valor) }}{{ pagamento.forma ? ` em ${pagamento.forma}` : '' }}</div>

      <table class="itens">
        <thead>
          <tr>
            <th class="text-left">Acerto</th>
            <th class="text-left">Cliente</th>
            <th class="text-left">Parcela</th>
            <th class="text-left">Vencimento</th>
            <th class="text-right">Comissão</th>
            <th class="text-right">Baixado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="l in pagamento.linhas" :key="l.id">
            <td>{{ l.acerto }}</td>
            <td>{{ l.cliente }}</td>
            <td>{{ l.parcela }}</td>
            <td>{{ formatarDataHora(l.vencimento).slice(0, 10) }}</td>
            <td class="text-right">{{ formatarMoeda(l.valor) }}</td>
            <td class="text-right">{{ formatarMoeda(l.baixado) }}</td>
          </tr>
        </tbody>
      </table>

      <div class="assinatura">
        <div>Recebi o valor acima, referente às comissões indicadas.</div>
        <div class="linha-assinatura">{{ pagamento.representante.cliente.nome }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarMoeda } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const rota = useRoute()
const sessao = useSessaoStore()
const pagamento = ref(null)
const erro = ref('')

function imprimir() {
  window.print()
}

onMounted(async () => {
  try {
    pagamento.value = (await api.get(`/consignacao/comissoes/pagamentos/${rota.params.id}`)).data
  } catch (e) {
    erro.value = mensagemDeErro(e)
    return
  }
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
.linha-assinatura {
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
