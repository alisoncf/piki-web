<template>
  <!-- índice das partes de uma ficha de página única: fica preso abaixo do cabeçalho enquanto a página rola -->
  <nav ref="barra" class="indice-ficha row no-wrap q-mb-md" :style="{ top: `${topo}px` }" aria-label="Partes da ficha">
    <q-btn
      v-for="s in secoes"
      :key="s.id"
      flat
      dense
      no-caps
      :label="s.titulo"
      class="indice-ficha__item"
      :class="{ 'indice-ficha__ativo': s.id === ativa }"
      :aria-current="s.id === ativa ? 'location' : undefined"
      @click="ir(s.id)"
    />
  </nav>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  // [{ id, titulo }]: id é o do elemento da seção na página, na ordem em que aparecem
  secoes: { type: Array, required: true },
})

const barra = ref(null)
const topo = ref(0)
const ativa = ref(props.secoes[0]?.id ?? null)
let travadoAte = 0 // durante a rolagem pedida pelo clique, a seção clicada continua marcada

// a seção fica logo abaixo do cabeçalho e do índice
function margem() {
  return topo.value + (barra.value?.offsetHeight ?? 0) + 8
}

function ir(id) {
  const alvo = document.getElementById(id)
  if (!alvo) return
  ativa.value = id
  travadoAte = Date.now() + 800
  window.scrollTo({ top: alvo.getBoundingClientRect().top + window.scrollY - margem(), behavior: 'smooth' })
}

// marca a última seção que já passou do topo
function atualizar() {
  if (Date.now() < travadoAte) return
  let atual = props.secoes[0]?.id ?? null
  for (const s of props.secoes) {
    const el = document.getElementById(s.id)
    if (el && el.getBoundingClientRect().top - margem() <= 1) atual = s.id
  }
  ativa.value = atual
}

onMounted(() => {
  topo.value = document.querySelector('.q-header')?.offsetHeight ?? 0
  window.addEventListener('scroll', atualizar, { passive: true })
})
onBeforeUnmount(() => window.removeEventListener('scroll', atualizar))
</script>

<style scoped>
.indice-ficha {
  position: sticky;
  z-index: 1;
  gap: 4px;
  overflow-x: auto;
  margin-left: -4px;
  padding: 8px 4px;
  background: var(--piki-fundo);
  border-bottom: 1px solid var(--piki-borda);
}
.indice-ficha__item {
  flex: none;
  color: var(--piki-texto-suave, #5f5f66);
}
.indice-ficha__ativo {
  color: var(--q-primary);
  background: color-mix(in srgb, var(--q-primary) 10%, transparent);
}
</style>
