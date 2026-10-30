<template>
  <div class="pagina-centralizada column">
    <marca-loja :tamanho="44" class="q-mb-xl" />
    <div class="text-h2 text-weight-bold text-primary">404</div>
    <div class="text-suave q-mb-lg">Esta página não existe.</div>
    <q-btn color="primary" unelevated no-caps label="Voltar ao início" to="/" />
  </div>
</template>

<script setup>
import MarcaLoja from '@/componentes/MarcaLoja.vue'
</script>
