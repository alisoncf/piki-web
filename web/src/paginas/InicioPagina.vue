<template>
  <q-page padding>
    <div class="q-mb-lg">
      <div class="piki-titulo">Bom trabalho, {{ primeiroNome }}!</div>
      <div class="text-suave">Você está em <strong>{{ sessao.empresa?.nome }}</strong>.</div>
    </div>

    <div class="row q-col-gutter-md">
      <div v-for="atalho in atalhos" :key="atalho.rota" class="col-12 col-sm-6 col-md-4 col-lg-3">
        <router-link :to="atalho.rota" class="cartao piki-atalho row items-center no-wrap q-pa-md" style="text-decoration: none; color: inherit">
          <div class="piki-atalho__icone q-mr-md"><q-icon :name="atalho.icone" size="24px" /></div>
          <div>
            <div class="text-subtitle1 text-weight-medium">{{ atalho.titulo }}</div>
            <div class="text-caption text-suave">{{ atalho.grupo }}</div>
          </div>
        </router-link>
      </div>
    </div>

    <q-banner v-if="!atalhos.length" class="cartao text-suave">
      <template #avatar><q-icon name="lock_clock" color="primary" /></template>
      Ainda não há telas liberadas para você nesta empresa.
    </q-banner>
  </q-page>
</template>

<script setup>
import { computed } from 'vue'

import { filtrarMenu, MENU } from '@/menu'
import { useSessaoStore } from '@/stores/sessao'

const sessao = useSessaoStore()
const primeiroNome = computed(() => (sessao.usuario?.nome || '').split(' ')[0])

// as telas liberadas, exceto o próprio início
const atalhos = computed(() =>
  filtrarMenu(MENU, sessao.pode).flatMap((item) =>
    item.filhos ? item.filhos.map((f) => ({ ...f, grupo: item.titulo })) : [],
  ),
)
</script>
