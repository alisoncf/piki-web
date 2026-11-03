<template>
  <lista-nomes
    titulo="Caixas da loja"
    item="caixa"
    url="/caixas"
    permissao-editar="caixa.configurar"
    :tamanho="30"
    :campo-numero="{ chave: 'serie_nfe', rotulo: 'Série das notas', dica: 'NFC-e e NF-e emitidas neste caixa; como no VB6, 101 é o caixa 01' }"
  />
</template>

<script setup>
import ListaNomes from '@/componentes/ListaNomes.vue'
</script>
