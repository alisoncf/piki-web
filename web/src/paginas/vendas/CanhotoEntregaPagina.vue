<template>
  <div class="canhoto">
    <div class="sem-impressao row items-center q-gutter-sm q-pa-md">
      <q-btn flat no-caps icon="arrow_back" label="Voltar para a venda" :to="{ name: 'venda', params: { id: rota.params.id } }" />
      <q-space />
      <q-btn unelevated no-caps color="primary" icon="print" label="Imprimir" :disable="!venda?.entrega" @click="imprimir" />
    </div>

    <div v-if="erro" class="q-pa-lg text-negative">{{ erro }}</div>
    <div v-else-if="!venda" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <div v-else-if="!venda.entrega" class="q-pa-lg">Esta venda não tem entrega.</div>
    <div v-else class="folha">
      <!-- duas vias: a do entregador e a que volta assinada para a loja -->
      <div v-for="via in ['Via da loja (volta assinada)', 'Via do entregador']" :key="via" class="via">
        <div class="row justify-between items-start">
          <div>
            <div class="titulo">Entrega · venda {{ venda.numero }}</div>
            <div class="pequeno">{{ sessao.empresa?.nome }} · {{ formatarDataHora(venda.recebida_em ?? venda.criado_em) }}</div>
          </div>
          <div class="pequeno text-right">{{ via }}</div>
        </div>

        <div class="bloco">
          <div class="rotulo">Entregar para</div>
          <div class="destaque">{{ venda.comprador ?? venda.cliente?.nome }}</div>
          <div>{{ endereco }}</div>
          <div v-if="venda.entrega.ponto_referencia">Referência: {{ venda.entrega.ponto_referencia }}</div>
          <div v-if="telefone">Telefone: {{ formatarTelefone(telefone) }}</div>
        </div>

        <table class="itens">
          <thead><tr><th class="text-left">Produto</th><th class="text-right">Qtd.</th></tr></thead>
          <tbody>
            <tr v-for="item in venda.itens" :key="item.id">
              <td>{{ formatarCodigoProduto(item.produto.codigo) }} · {{ item.descricao }}</td>
              <td class="text-right">{{ formatarQuantidade(item.quantidade) }} {{ item.produto.unidade }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="venda.observacao" class="pequeno">Observação: {{ venda.observacao }}</div>
        <div class="pequeno">{{ venda.situacao === 'recebida' ? 'Venda paga na loja (a taxa de entrega também).' : 'Venda ainda não recebida no caixa.' }}</div>

        <div class="assinatura">
          <div>Recebi as mercadorias acima em ____/____/______</div>
          <div class="linha">Assinatura de quem recebeu</div>
          <div class="linha">Entregador</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCodigoProduto, formatarDataHora, formatarQuantidade, formatarTelefone } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const rota = useRoute()
const sessao = useSessaoStore()
const venda = ref(null)
const erro = ref('')

const endereco = computed(() => {
  const e = venda.value?.entrega
  if (!e) return ''
  const rua = [e.logradouro, e.numero && `nº ${e.numero}`, e.complemento].filter(Boolean).join(' ')
  const cidade = e.cidade ? `${e.cidade.nome}/${e.cidade.uf}` : ''
  return [rua, e.bairro, cidade, e.cep && `CEP ${e.cep}`].filter(Boolean).join(' - ')
})
const telefone = computed(() => venda.value?.entrega?.telefone || venda.value?.consumidor?.telefone || venda.value?.cliente?.telefones?.[0]?.numero)

function imprimir() {
  window.print()
}

onMounted(async () => {
  try {
    venda.value = (await api.get(`/vendas/${rota.params.id}`)).data
  } catch (e) {
    erro.value = mensagemDeErro(e)
    return
  }
  // aberto logo depois de receber: já chama a janela de impressão
  if (rota.query.imprimir && venda.value.entrega) {
    await nextTick()
    imprimir()
  }
})
</script>

<style scoped>
.canhoto {
  max-width: 190mm;
  margin: 0 auto;
  background: #fff;
  color: #000;
  font-size: 12px;
}
.via {
  border-bottom: 1px dashed #888;
  padding: 5mm 0;
  page-break-inside: avoid;
  break-inside: avoid;
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
  margin-top: 4mm;
}
.assinatura .linha {
  margin-top: 8mm;
  border-top: 1px solid #000;
  width: 70mm;
  font-size: 10px;
}
@media print {
  .sem-impressao {
    display: none !important;
  }
  .canhoto {
    max-width: none;
  }
}
</style>
