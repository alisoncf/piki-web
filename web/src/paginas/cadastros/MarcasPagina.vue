<template>
  <lista-nomes titulo="Marcas" item="marca" feminino url="/marcas" permissao-editar="produtos.editar" :tamanho="50" />
</template>

<script setup>
import ListaNomes from '@/componentes/ListaNomes.vue'
</script>
