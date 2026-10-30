<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn flat round dense icon="menu" aria-label="Abrir menu" @click="menuAberto = !menuAberto" />
        <q-toolbar-title class="text-weight-bold">Piki</q-toolbar-title>

        <!-- empresa ativa e troca rápida -->
        <q-btn
          v-if="sessao.podeTrocarEmpresa"
          flat
          no-caps
          icon="store"
          :label="sessao.empresa?.nome"
          :loading="trocando"
          aria-label="Trocar de empresa"
        >
          <q-menu anchor="bottom right" self="top right">
            <q-list style="min-width: 220px">
              <q-item-label header>Trocar de empresa</q-item-label>
              <q-item
                v-for="emp in sessao.empresas"
                :key="emp.id"
                v-close-popup
                clickable
                :active="emp.id === sessao.empresa?.id"
                @click="trocar(emp)"
              >
                <q-item-section avatar>
                  <q-avatar color="primary" text-color="white" size="sm">{{ emp.codigo }}</q-avatar>
                </q-item-section>
                <q-item-section>{{ emp.nome }}</q-item-section>
                <q-item-section v-if="emp.id === sessao.empresa?.id" side>
                  <q-icon name="check" color="primary" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
        <div v-else class="q-px-sm row items-center no-wrap">
          <q-icon name="store" class="q-mr-xs" />{{ sessao.empresa?.nome }}
        </div>

        <!-- usuário -->
        <q-btn flat round dense icon="account_circle" class="q-ml-sm" aria-label="Usuário">
          <q-menu anchor="bottom right" self="top right">
            <q-list style="min-width: 200px">
              <q-item>
                <q-item-section>
                  <q-item-label>{{ sessao.usuario?.nome }}</q-item-label>
                  <q-item-label caption>{{ sessao.usuario?.login }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-separator />
              <q-item v-close-popup clickable @click="sair">
                <q-item-section avatar><q-icon name="logout" /></q-item-section>
                <q-item-section>Sair</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="menuAberto" show-if-above bordered :width="240">
      <q-list padding>
        <template v-for="item in menu" :key="item.titulo">
          <q-expansion-item v-if="item.filhos" :icon="item.icone" :label="item.titulo" default-opened>
            <q-item
              v-for="filho in item.filhos"
              :key="filho.rota"
              :to="filho.rota"
              exact
              clickable
              class="q-pl-lg"
              active-class="text-primary bg-blue-1"
            >
              <q-item-section avatar><q-icon :name="filho.icone" /></q-item-section>
              <q-item-section>{{ filho.titulo }}</q-item-section>
            </q-item>
          </q-expansion-item>
          <q-item v-else :to="item.rota" exact clickable active-class="text-primary bg-blue-1">
            <q-item-section avatar><q-icon :name="item.icone" /></q-item-section>
            <q-item-section>{{ item.titulo }}</q-item-section>
          </q-item>
        </template>
      </q-list>
    </q-drawer>

    <q-page-container>
      <!-- a chave remonta a página ao trocar de empresa, para recarregar os dados -->
      <router-view :key="sessao.empresa?.id" />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { filtrarMenu, MENU } from '@/menu'
import { mensagemDeErro } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const sessao = useSessaoStore()
const roteador = useRouter()
const rota = useRoute()
const $q = useQuasar()

const menuAberto = ref(false)
const trocando = ref(false)
const menu = computed(() => filtrarMenu(MENU, sessao.pode))

async function trocar(emp) {
  if (emp.id === sessao.empresa?.id) return
  trocando.value = true
  try {
    await sessao.escolherEmpresa(emp.id)
    $q.notify({ type: 'positive', message: `Agora em ${emp.nome}`, timeout: 1500 })
    // se a tela atual não é permitida na nova empresa, volta ao início
    if (rota.meta.permissao && !sessao.pode(rota.meta.permissao)) await roteador.push({ name: 'inicio' })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    trocando.value = false
  }
}

function sair() {
  sessao.sair()
  roteador.push({ name: 'login' })
}
</script>
