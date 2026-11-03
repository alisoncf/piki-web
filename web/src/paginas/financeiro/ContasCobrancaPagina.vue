<template>
  <!-- onde os carnês ficam para cobrar: a Geral (na loja), os cobradores, o advogado, os balanços... (D27) -->
  <lista-nomes titulo="Contas de cobrança" item="conta de cobrança" url="/receber/contas-cobranca" permissao-editar="receber.cobranca" feminino :tamanho="40" />
</template>

<script setup>
import ListaNomes from '@/componentes/ListaNomes.vue'
</script>
