<template>
  <div class="assinatura-piki row items-center no-wrap">
    <img :src="SISTEMA.icone" width="20" height="20" alt="" />
    <span>{{ SISTEMA.nome }} · gestão comercial</span>
  </div>
</template>

<script setup>
import { SISTEMA } from '@/marca'
</script>

<style scoped>
.assinatura-piki {
  gap: 8px;
  font-size: 12px;
  opacity: 0.75;
}
</style>
