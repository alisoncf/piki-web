<template>
  <!-- item do menu lateral; grupos se desenham de novo para cada filho, em qualquer nível -->
  <q-expansion-item
    v-if="item.filhos"
    :icon="item.icone"
    :label="item.titulo"
    :default-opened="contemRota(item, rota.path)"
    :header-style="recuo"
    :header-class="{ 'piki-menu__grupo-ativo': contemRota(item, rota.path) }"
    dark
  >
    <item-menu v-for="filho in item.filhos" :key="filho.titulo" :item="filho" :nivel="nivel + 1" />
  </q-expansion-item>
  <q-item v-else :to="item.rota" clickable :active="contemRota(item, rota.path)" active-class="piki-menu__ativo" :style="recuo">
    <q-item-section avatar><q-icon :name="item.icone" :size="nivel ? '20px' : undefined" /></q-item-section>
    <q-item-section>{{ item.titulo }}</q-item-section>
  </q-item>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { contemRota } from '@/menu'

const props = defineProps({
  item: { type: Object, required: true },
  nivel: { type: Number, default: 0 },
})

const rota = useRoute()
const recuo = computed(() => ({ paddingLeft: `${16 + props.nivel * 14}px` }))
</script>
