<template>
  <!-- escolha numa lista grande (setores, órgãos): digita parte do nome para filtrar -->
  <q-select
    :model-value="modelValue"
    outlined
    use-input
    input-debounce="150"
    :options="visiveis"
    option-value="id"
    :option-label="rotulo"
    emit-value
    map-options
    clearable
    v-bind="$attrs"
    @update:model-value="(v) => emit('update:modelValue', v)"
    @filter="filtrar"
  >
    <template #no-option>
      <q-item><q-item-section class="text-suave">Nada encontrado</q-item-section></q-item>
    </template>
  </q-select>
</template>

<script setup>
import { computed, ref } from 'vue'

import { semAcentos } from '@/servicos/formatos'

const props = defineProps({
  modelValue: { type: Number, default: null },
  opcoes: { type: Array, required: true },
  // texto mostrado para cada opção; por padrão, o nome
  rotulo: { type: Function, default: (o) => o?.nome ?? '' },
  // mostra no máximo isto enquanto filtra, para a lista não pesar
  limite: { type: Number, default: 50 },
})
const emit = defineEmits(['update:modelValue'])
defineOptions({ inheritAttrs: false })

const filtradas = ref([])

// a opção escolhida fica sempre na lista, para o campo mostrar o nome dela
const visiveis = computed(() => {
  const escolhida = props.opcoes.find((o) => o.id === props.modelValue)
  return escolhida && !filtradas.value.includes(escolhida) ? [escolhida, ...filtradas.value] : filtradas.value
})

function filtrar(termo, atualizar) {
  atualizar(() => {
    const t = semAcentos(termo)
    filtradas.value = props.opcoes.filter((o) => !t || semAcentos(props.rotulo(o)).includes(t)).slice(0, props.limite)
  })
}
</script>
