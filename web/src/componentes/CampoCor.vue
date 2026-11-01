<template>
  <!-- cor em #rrggbb: digitada ou escolhida na paleta que abre pelo ícone -->
  <q-input
    :model-value="modelValue"
    outlined
    maxlength="7"
    :rules="[(v) => /^#[0-9a-fA-F]{6}$/.test(v || '') || 'Use o formato #rrggbb']"
    v-bind="$attrs"
    @update:model-value="(v) => emit('update:modelValue', v?.toLowerCase())"
  >
    <template #prepend>
      <div class="campo-cor__amostra" :style="{ background: modelValue }" />
    </template>
    <template #append>
      <q-btn flat round dense icon="colorize" aria-label="Escolher a cor">
        <q-popup-proxy cover transition-show="scale" transition-hide="scale">
          <q-color
            :model-value="modelValue"
            no-header-tabs
            format-model="hex"
            @update:model-value="(v) => emit('update:modelValue', v?.toLowerCase())"
          />
        </q-popup-proxy>
      </q-btn>
    </template>
  </q-input>
</template>

<script setup>
defineProps({ modelValue: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue'])
defineOptions({ inheritAttrs: false })
</script>

<style scoped>
.campo-cor__amostra {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.15);
}
</style>
