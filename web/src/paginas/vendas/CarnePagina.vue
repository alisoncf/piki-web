<template>
  <div class="carne">
    <div class="sem-impressao row items-center q-gutter-sm q-pa-md">
      <q-btn flat no-caps icon="arrow_back" label="Voltar para a venda" :to="{ name: 'venda', params: { id: rota.params.id } }" />
      <q-space />
      <q-btn unelevated no-caps color="primary" icon="print" label="Imprimir" :disable="!dados" @click="imprimir" />
    </div>

    <div v-if="erro" class="q-pa-lg text-negative">{{ erro }}</div>
    <div v-else-if="!dados" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <template v-else>
      <div v-for="p in dados.carne.parcelas" :key="p.numero" class="parcela">
        <!-- fica na loja -->
        <div class="canhoto">
          <div class="loja">{{ dados.loja.nome }}</div>
          <div class="campo"><span>Carnê</span>{{ dados.carne.id }} · venda {{ dados.venda }}</div>
          <div class="campo"><span>Parcela</span>{{ p.numero }}/{{ dados.carne.parcelas.length }}</div>
          <div class="campo"><span>Vencimento</span><strong>{{ data(p.vencimento) }}</strong></div>
          <div class="campo"><span>Valor</span><strong>{{ formatarMoeda(p.valor) }}</strong></div>
          <div class="campo"><span>Cliente</span>{{ dados.cliente.nome }}</div>
          <div class="campo"><span>Juros</span>__________</div>
          <div class="campo"><span>Total pago</span>__________</div>
          <div class="campo"><span>Pago em</span>____/____/______</div>
        </div>

        <!-- fica com o cliente -->
        <div class="recibo">
          <div class="row justify-between">
            <div>
              <div class="loja">{{ dados.loja.nome }}</div>
              <div class="pequeno">
                <template v-if="dados.loja.cnpj">CNPJ {{ formatarCnpj(dados.loja.cnpj) }} · </template>{{ dados.loja.endereco }}
                <template v-if="dados.loja.telefone"> · {{ formatarTelefone(dados.loja.telefone) }}</template>
              </div>
            </div>
            <div class="text-right">
              <div class="pequeno">Parcela</div>
              <div class="destaque">{{ p.numero }}/{{ dados.carne.parcelas.length }}</div>
            </div>
          </div>
          <div class="grade">
            <div class="campo"><span>Vencimento</span><strong class="destaque">{{ data(p.vencimento) }}</strong></div>
            <div class="campo"><span>Valor da parcela</span><strong class="destaque">{{ formatarMoeda(p.valor) }}</strong></div>
            <div class="campo"><span>Carnê</span>{{ dados.carne.id }}</div>
            <div class="campo"><span>Venda</span>{{ dados.venda }} de {{ formatarDataHora(dados.data).slice(0, 10) }}</div>
            <div class="campo"><span>Valor do carnê</span>{{ formatarMoeda(dados.carne.valor) }}</div>
            <div class="campo"><span>Juros de atraso</span>__________</div>
          </div>
          <div class="campo"><span>Cliente</span>{{ dados.cliente.nome }}<template v-if="dados.cliente.cpf_cnpj"> · CPF {{ formatarDocumento(dados.cliente.cpf_cnpj) }}</template></div>
          <div class="pequeno">{{ [dados.cliente.endereco, dados.cliente.cidade].filter(Boolean).join(' - ') }}</div>
          <div class="pequeno q-mt-xs">Pague na loja até o vencimento. Depois dele, a parcela pode ter juros de atraso.</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarCnpj, formatarDataHora, formatarDocumento, formatarMoeda, formatarTelefone } from '@/servicos/formatos'

const rota = useRoute()
const dados = ref(null)
const erro = ref('')

const data = (valor) => formatarDataHora(valor)

function imprimir() {
  window.print()
}

onMounted(async () => {
  try {
    dados.value = (await api.get(`/vendas/${rota.params.id}/carne`)).data
  } catch (e) {
    erro.value = mensagemDeErro(e)
    return
  }
  // aberto logo depois de receber: já chama a janela de impressão
  if (rota.query.imprimir) {
    await nextTick()
    imprimir()
  }
})
</script>

<style scoped>
.carne {
  max-width: 190mm;
  margin: 0 auto;
  background: #fff;
  color: #000;
  font-size: 12px;
}
.parcela {
  display: flex;
  border-bottom: 1px dashed #888;
  padding: 4mm 0;
  page-break-inside: avoid;
  break-inside: avoid;
}
.canhoto {
  width: 55mm;
  padding-right: 4mm;
  margin-right: 4mm;
  border-right: 1px dashed #888;
}
.recibo {
  flex: 1;
}
.loja {
  font-weight: 700;
  font-size: 13px;
}
.pequeno {
  font-size: 10px;
}
.destaque {
  font-size: 15px;
  font-weight: 700;
}
.campo span {
  display: block;
  font-size: 9px;
  text-transform: uppercase;
  color: #555;
}
.canhoto .campo {
  margin-top: 1.5mm;
}
.grade {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2mm;
  margin: 2mm 0;
}
@media print {
  .sem-impressao {
    display: none !important;
  }
  .carne {
    max-width: none;
  }
}
</style>
