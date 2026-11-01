<template>
  <q-layout>
    <q-page-container>
      <q-page class="pagina-centralizada column">
        <marca-loja :tamanho="44" class="q-mb-lg" />
        <div class="cartao cartao-estreito">
          <div class="q-pa-lg q-pb-md">
            <div class="piki-titulo">Olá, {{ primeiroNome }}</div>
            <div class="text-suave">Em qual empresa você vai trabalhar?</div>
          </div>

          <q-list separator class="q-px-sm">
            <q-item
              v-for="emp in sessao.empresas"
              :key="emp.id"
              clickable
              class="rounded-borders"
              :active="emp.id === sessao.empresa?.id"
              active-class="bg-primario-claro text-primary"
              :disable="!!enviando"
              @click="escolher(emp)"
            >
              <q-item-section avatar>
                <q-avatar text-color="white" size="40px" font-size="15px" class="text-weight-bold" :style="{ background: emp.tema.principal }">
                  {{ emp.codigo }}
                </q-avatar>
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">{{ emp.nome }}</q-item-label>
                <q-item-label v-if="emp.id === sessao.ultimaEmpresaId" caption>Última usada</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-spinner v-if="enviando === emp.id" color="primary" />
                <q-icon v-else name="chevron_right" />
              </q-item-section>
            </q-item>
          </q-list>

          <div class="row justify-end q-pa-sm">
            <q-btn flat no-caps color="grey-8" label="Sair" icon="logout" @click="sair" />
          </div>
        </div>
        <assinatura-piki class="q-mt-lg text-suave" />
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AssinaturaPiki from '@/componentes/AssinaturaPiki.vue'
import MarcaLoja from '@/componentes/MarcaLoja.vue'
import { mensagemDeErro } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const sessao = useSessaoStore()
const roteador = useRouter()
const rota = useRoute()
const $q = useQuasar()

const enviando = ref(null)
const primeiroNome = computed(() => (sessao.usuario?.nome || '').split(' ')[0])

async function escolher(emp) {
  enviando.value = emp.id
  try {
    await sessao.escolherEmpresa(emp.id)
    await roteador.push(rota.query.volta || '/')
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    enviando.value = null
  }
}

function sair() {
  sessao.sair()
  roteador.push({ name: 'login' })
}
</script>
