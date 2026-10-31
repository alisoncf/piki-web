<template>
  <!-- CEP com o botão que busca o endereço (Enter também busca) -->
  <q-input
    :model-value="modelValue"
    outlined
    mask="#####-###"
    unmasked-value
    v-bind="$attrs"
    @update:model-value="(v) => emit('update:modelValue', v)"
    @keydown.enter.prevent="pedir"
  >
    <template #append>
      <q-btn
        flat
        round
        dense
        icon="search"
        :loading="buscando"
        :disable="!completo"
        aria-label="Buscar o endereço do CEP"
        @click="pedir"
      >
        <q-tooltip>Buscar o endereço do CEP</q-tooltip>
      </q-btn>
    </template>
  </q-input>
</template>

<script setup>
import { computed } from 'vue'

import { soDigitos } from '@/servicos/formatos'

const props = defineProps({
  modelValue: { type: String, default: null },
  buscando: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'buscar'])
defineOptions({ inheritAttrs: false })

const completo = computed(() => soDigitos(props.modelValue).length === 8)

function pedir() {
  if (completo.value && !props.buscando) emit('buscar')
}
</script>
