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

<style scoped>
.marca-loja {
  gap: 10px;
}
.marca-loja img {
  border-radius: 22%;
  flex: none;
}
.marca-loja__nome {
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.05;
  color: var(--piki-primaria);
}
.marca-loja__complemento {
  font-weight: 600;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  line-height: 1.2;
  color: var(--piki-texto-suave);
}
.marca-loja--clara img {
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.35);
}
.marca-loja--clara .marca-loja__nome {
  color: #fff;
}
.marca-loja--clara .marca-loja__complemento {
  color: rgba(255, 255, 255, 0.7);
}
</style>
