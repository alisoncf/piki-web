<template>
  <!-- cidade do IBGE: busca na API enquanto digita (são 5.571), sem ligar para acentos -->
  <q-select
    :model-value="modelValue"
    outlined
    use-input
    input-debounce="250"
    :options="visiveis"
    option-value="id"
    :option-label="rotulo"
    emit-value
    map-options
    clearable
    label="Cidade"
    v-bind="$attrs"
    @update:model-value="escolher"
    @filter="filtrar"
  >
    <template #no-option>
      <q-item><q-item-section class="text-suave">Digite parte do nome da cidade</q-item-section></q-item>
    </template>
  </q-select>
</template>

<script setup>
import { computed, ref } from 'vue'

import { api } from '@/servicos/api'

const props = defineProps({
  modelValue: { type: Number, default: null },
  // a cidade já escolhida ({ id, nome, uf }), para o campo mostrar o nome antes de qualquer busca
  cidade: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'update:cidade'])
defineOptions({ inheritAttrs: false })

const encontradas = ref([])

const visiveis = computed(() => {
  const atual = props.cidade?.id === props.modelValue ? props.cidade : null
  return atual && !encontradas.value.some((c) => c.id === atual.id) ? [atual, ...encontradas.value] : encontradas.value
})

function rotulo(c) {
  return c ? `${c.nome} - ${c.uf}` : ''
}

async function filtrar(termo, atualizar, cancelar) {
  if (termo.trim().length < 2) {
    atualizar(() => (encontradas.value = []))
    return
  }
  try {
    const { data } = await api.get('/cidades', { params: { busca: termo, limite: 20 } })
    atualizar(() => (encontradas.value = data))
  } catch {
    cancelar()
  }
}

function escolher(id) {
  emit('update:modelValue', id)
  emit('update:cidade', visiveis.value.find((c) => c.id === id) ?? null)
}
</script>
