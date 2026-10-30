<template>
  <router-view />
</template>

<script setup>
import { watchEffect } from 'vue'

import { aplicarEmpresa } from '@/marca'
import { useSessaoStore } from '@/stores/sessao'

const sessao = useSessaoStore()
watchEffect(() => aplicarEmpresa(sessao.empresa))
</script>
