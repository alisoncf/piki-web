<template>
  <lista-nomes titulo="Cobradores" item="cobrador" url="/cobradores" permissao-editar="clientes.editar" :tamanho="40" />
</template>

<script setup>
import ListaNomes from '@/componentes/ListaNomes.vue'
</script>
