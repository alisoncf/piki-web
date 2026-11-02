<template>
  <lista-nomes titulo="Caixas da loja" item="caixa" url="/caixas" permissao-editar="caixa.configurar" :tamanho="30" />
</template>

<script setup>
import ListaNomes from '@/componentes/ListaNomes.vue'
</script>
