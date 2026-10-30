<template>
  <lista-nomes titulo="Grupos de clientes" item="grupo" url="/grupos-clientes" permissao-editar="clientes.editar" :tamanho="40" />
</template>

<script setup>
import ListaNomes from '@/componentes/ListaNomes.vue'
</script>
