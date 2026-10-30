<template>
  <q-page padding>
    <div class="text-h5 q-mb-xs">Bom trabalho, {{ primeiroNome }}!</div>
    <div class="text-grey-7 q-mb-lg">Você está em <strong>{{ sessao.empresa?.nome }}</strong>.</div>

    <div class="row q-col-gutter-md">
      <div v-for="atalho in atalhos" :key="atalho.rota" class="col-12 col-sm-6 col-md-4">
        <q-card flat bordered class="cursor-pointer" @click="$router.push(atalho.rota)">
          <q-card-section class="row items-center no-wrap">
            <q-icon :name="atalho.icone" size="md" color="primary" class="q-mr-md" />
            <div>
              <div class="text-subtitle1">{{ atalho.titulo }}</div>
              <div class="text-caption text-grey-7">{{ atalho.grupo }}</div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <q-banner v-if="!atalhos.length" class="bg-grey-2 text-grey-8" rounded>
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
