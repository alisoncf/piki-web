<template>
  <q-layout>
    <q-page-container>
      <q-page class="pagina-centralizada">
        <q-card class="cartao-estreito" flat bordered>
          <q-card-section>
            <div class="text-h6">Olá, {{ primeiroNome }}</div>
            <div class="text-grey-7">Em qual empresa você vai trabalhar?</div>
          </q-card-section>

          <q-list separator>
            <q-item
              v-for="emp in sessao.empresas"
              :key="emp.id"
              clickable
              :active="emp.id === sessao.empresa?.id"
              active-class="bg-blue-1"
              :disable="!!enviando"
              @click="escolher(emp)"
            >
              <q-item-section avatar>
                <q-avatar color="primary" text-color="white" size="md">{{ emp.codigo }}</q-avatar>
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ emp.nome }}</q-item-label>
                <q-item-label v-if="emp.id === sessao.ultimaEmpresaId" caption>Última usada</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-spinner v-if="enviando === emp.id" color="primary" />
                <q-icon v-else name="chevron_right" />
              </q-item-section>
            </q-item>
          </q-list>

          <q-card-actions align="right">
            <q-btn flat color="grey-8" label="Sair" icon="logout" @click="sair" />
          </q-card-actions>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

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
