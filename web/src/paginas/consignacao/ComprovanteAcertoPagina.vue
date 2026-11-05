<template>
  <!-- o comprovante do acerto (D30): as peças, o valor negociado, a comissão (ou o desconto) e as duplicatas geradas;
       o representante assina -->
  <div class="comprovante">
    <div class="sem-impressao row items-center q-gutter-sm q-pa-md">
      <q-btn flat no-caps icon="arrow_back" label="Acertos" :to="{ name: 'transferencias', query: { aba: 'acertos' } }" />
      <q-space />
      <q-btn v-if="acerto?.conta_id" flat no-caps color="primary" icon="receipt_long" label="Carnê" :to="{ name: 'carne-acerto', params: { id: acerto.id } }" />
      <q-btn unelevated no-caps color="primary" icon="print" label="Imprimir" :disable="!acerto" @click="imprimir" />
    </div>

    <div v-if="erro" class="q-pa-lg text-negative">{{ erro }}</div>
    <div v-else-if="!acerto" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <div v-else class="folha">
      <div class="row justify-between items-start">
        <div>
          <div class="titulo">Acerto de consignado nº {{ acerto.numero }}{{ acerto.queima ? ' (queima)' : '' }}</div>
          <div class="pequeno">{{ sessao.empresa?.nome }} · {{ formatarDataHora(acerto.confirmada_em ?? acerto.criado_em) }}</div>
        </div>
        <div class="pequeno text-right">
          <div>{{ acerto.situacao === 'aberta' ? 'NÃO CONFIRMADO' : `Atendido por ${acerto.atendida_por.nome}` }}</div>
          <div v-if="acerto.autorizada_por">Acima do limite, autorizado por {{ acerto.autorizada_por.nome }}</div>
        </div>
      </div>

      <div class="row q-col-gutter-md bloco">
        <div class="col">
          <div class="rotulo">Representante</div>
          <div class="destaque">{{ acerto.representante.codigo }} · {{ acerto.representante.cliente.nome }}</div>
        </div>
        <div class="col">
          <div class="rotulo">{{ acerto.para === 'cliente' ? 'Cliente' : 'Acerto para o próprio representante' }}</div>
          <div class="destaque">{{ acerto.cliente?.nome }}</div>
          <div v-if="acerto.cliente?.cpf_cnpj">CPF {{ formatarDocumento(acerto.cliente.cpf_cnpj) }}</div>
        </div>
      </div>

      <table class="itens">
        <thead>
          <tr>
            <th class="text-left">Produto</th>
            <th class="text-left">Transferência</th>
            <th class="text-right">Qtd.</th>
            <th class="text-right">Preço</th>
            <th class="text-right">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in acerto.itens" :key="item.id">
            <td>{{ formatarCodigoProduto(item.item_transferencia.produto.codigo) }} · {{ item.item_transferencia.descricao }}</td>
            <td>{{ item.item_transferencia.transferencia.numero }}</td>
            <td class="text-right">{{ formatarQuantidade(item.quantidade) }} {{ item.item_transferencia.produto.unidade }}</td>
            <td class="text-right">{{ formatarMoeda(item.preco) }}</td>
            <td class="text-right">{{ formatarMoeda(item.total) }}</td>
          </tr>
        </tbody>
      </table>

      <div class="row q-col-gutter-md bloco">
        <div class="col-6">
          <div class="linha"><span>Total</span><span>{{ formatarMoeda(acerto.total_inicial) }}</span></div>
          <div class="linha"><span>Valor negociado</span><span>{{ formatarMoeda(acerto.negociado) }}</span></div>
          <div class="linha"><span>Diferença</span><span>{{ formatarMoeda(acerto.diferenca) }}</span></div>
          <div class="linha">
            <span>{{ acerto.para === 'representante' ? 'Desconto' : 'Comissão' }} ({{ Number(acerto.percentual).toLocaleString('pt-BR') }}%)</span>
            <span>{{ formatarMoeda(acerto.comissao) }}</span>
          </div>
          <div class="linha destaque"><span>Valor do acerto</span><span>{{ formatarMoeda(acerto.valor) }}</span></div>
        </div>
        <div class="col-6">
          <div class="rotulo">{{ acerto.pagamento === 'vista' ? 'Pago à vista' : acerto.nome_comissao }}</div>
          <div v-for="(pg, i) in acerto.pagamentos" :key="i" class="linha">
            <span>{{ acerto.pagamento === 'prazo' ? 'Entrada · ' : '' }}{{ pg.forma_pagamento.nome }}{{ pg.parcelas > 1 ? ` ${pg.parcelas}x` : '' }}</span>
            <span>{{ formatarMoeda(pg.valor) }}</span>
          </div>
          <template v-if="acerto.carne.length">
            <div class="rotulo q-mt-xs">Duplicatas geradas</div>
            <div v-for="p in acerto.carne" :key="p.id" class="linha">
              <span>{{ p.numero }}/{{ acerto.carne.length }} · {{ formatarData(p.vencimento) }}</span>
              <span>{{ formatarMoeda(p.valor) }}</span>
            </div>
          </template>
        </div>
      </div>

      <div class="assinatura">
        <div v-if="acerto.para === 'cliente'">Acertei os produtos acima, vendidos a {{ acerto.cliente?.nome }}, pelos valores indicados.</div>
        <div v-else>Acertei os produtos acima para mim, pelos valores indicados, e assumo a dívida.</div>
        <div class="linha-assinatura">{{ acerto.representante.cliente.nome }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCodigoProduto, formatarDataHora, formatarDocumento, formatarMoeda, formatarQuantidade } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const rota = useRoute()
const sessao = useSessaoStore()
const acerto = ref(null)
const erro = ref('')

const formatarData = (valor) => formatarDataHora(valor).slice(0, 10)

function imprimir() {
  window.print()
}

onMounted(async () => {
  try {
    acerto.value = (await api.get(`/consignacao/acertos/${rota.params.id}`)).data
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
.linha {
  display: flex;
  justify-content: space-between;
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
