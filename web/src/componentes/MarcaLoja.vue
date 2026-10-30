<template>
  <div class="marca-loja row items-center no-wrap" :class="{ 'marca-loja--clara': clara }">
    <img :src="LOJA.logo" :width="tamanho" :height="tamanho" alt="" />
    <div v-if="!soLogo" class="column">
      <span class="marca-loja__nome" :style="{ fontSize: `${tamanho * 0.5}px` }">{{ LOJA.nome }}</span>
      <span class="marca-loja__complemento" :style="{ fontSize: `${Math.max(9, tamanho * 0.24)}px` }">
        {{ LOJA.complemento }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { LOJA } from '@/marca'

defineProps({
  tamanho: { type: Number, default: 32 },
  /** para fundos escuros */
  clara: { type: Boolean, default: false },
  soLogo: { type: Boolean, default: false },
})
</script>
