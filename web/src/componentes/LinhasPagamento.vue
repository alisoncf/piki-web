<template>
  <!-- como o cliente paga no caixa: uma linha por forma; com dinheiro, o valor que ele deu e o troco -->
  <div>
    <div v-for="(pg, i) in linhas" :key="i" class="row q-col-gutter-sm items-start q-mb-sm">
      <q-select
        v-model="pg.forma_pagamento_id"
        outlined
        dense
        label="Forma"
        :options="formas"
        option-value="id"
        option-label="nome"
        emit-value
        map-options
        class="col-12 col-sm-5"
        @update:model-value="pg.parcelas = 1"
      />
      <q-input v-model="pg.valor" outlined dense type="number" step="0.01" min="0" prefix="R$" label="Valor" class="col">
        <template v-if="falta > 0" #append>
          <q-btn flat dense no-caps size="sm" color="primary" label="Restante" @click="pg.valor = (Number(pg.valor || 0) + falta).toFixed(2)" />
        </template>
      </q-input>
      <q-select
        v-if="comParcelas && formaPorId(pg.forma_pagamento_id)?.parcelas > 1"
        v-model="pg.parcelas"
        outlined
        dense
        label="Parcelas"
        :options="opcoesParcelas(formaPorId(pg.forma_pagamento_id))"
        emit-value
        map-options
        class="col-3"
      />
      <div class="col-auto"><q-btn flat round dense icon="delete" aria-label="Tirar" @click="linhas.splice(i, 1)" /></div>
    </div>
    <div v-if="dinheiro > 0" class="row q-col-gutter-sm items-center q-mt-sm">
      <q-input
        :model-value="valorRecebido"
        outlined
        autofocus
        type="number"
        step="0.01"
        min="0"
        prefix="R$"
        label="Valor que o cliente deu (dinheiro)"
        class="col-12 col-sm-6"
        @update:model-value="(v) => emit('update:valorRecebido', v)"
      />
      <div v-if="trocoAtual > 0" class="col text-h6">Troco {{ formatarMoeda(trocoAtual) }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import { formatarMoeda } from '@/servicos/formatos'
import { noDinheiro, troco } from '@/servicos/pagamentos'

// as linhas são do pai (um array reativo); aqui só se mexe nos campos delas
const props = defineProps({
  linhas: { type: Array, required: true },
  formas: { type: Array, required: true }, // as que podem ser usadas aqui (sem o crediário)
  falta: { type: Number, default: 0 }, // o que falta lançar, para o botão "Restante"
  valorRecebido: { type: [String, Number], default: '' },
  comParcelas: { type: Boolean, default: false }, // parcelas no cartão de crédito
})
const emit = defineEmits(['update:valorRecebido'])

const dinheiro = computed(() => noDinheiro(props.linhas, props.formas))
const trocoAtual = computed(() => troco(props.valorRecebido, dinheiro.value))

function formaPorId(id) {
  return props.formas.find((f) => f.id === id) ?? null
}

function opcoesParcelas(f) {
  return Array.from({ length: f?.parcelas ?? 1 }, (_, i) => ({
    value: i + 1,
    label: i + 1 > f.parcelas_sem_autorizacao ? `${i + 1}x (pede autorização)` : `${i + 1}x`,
  }))
}
</script>
