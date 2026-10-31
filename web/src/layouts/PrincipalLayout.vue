<template>
  <q-layout view="hHh lpR fFf">
    <q-header class="piki-cabecalho">
      <q-toolbar class="q-gutter-x-sm">
        <q-btn flat round dense icon="menu" color="grey-8" aria-label="Abrir menu" @click="menuAberto = !menuAberto" />
        <router-link to="/" class="q-mr-auto" aria-label="Início" style="text-decoration: none">
          <marca-loja :tamanho="34" />
        </router-link>

        <!-- empresa ativa e troca rápida -->
        <q-btn
          v-if="sessao.podeTrocarEmpresa"
          flat
          no-caps
          class="piki-empresa"
          :loading="trocando"
          aria-label="Trocar de empresa"
        >
          <q-avatar text-color="white" size="22px" font-size="11px" class="q-mr-sm" :style="{ background: sessao.empresa?.cor }">
            {{ sessao.empresa?.codigo }}
          </q-avatar>
          <span class="text-weight-medium">{{ sessao.empresa?.nome }}</span>
          <q-icon name="expand_more" size="18px" class="q-ml-xs text-suave" />
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
                  <q-avatar text-color="white" size="sm" :style="{ background: emp.cor }">{{ emp.codigo }}</q-avatar>
                </q-item-section>
                <q-item-section>{{ emp.nome }}</q-item-section>
                <q-item-section v-if="emp.id === sessao.empresa?.id" side>
                  <q-icon name="check" color="primary" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
        <div v-else class="piki-empresa q-px-sm q-py-xs row items-center no-wrap">
          <q-avatar text-color="white" size="22px" font-size="11px" class="q-mr-sm" :style="{ background: sessao.empresa?.cor }">
            {{ sessao.empresa?.codigo }}
          </q-avatar>
          <span class="text-weight-medium">{{ sessao.empresa?.nome }}</span>
        </div>

        <!-- usuário -->
        <q-btn flat round dense aria-label="Usuário">
          <q-avatar color="accent" text-color="dark" size="34px" font-size="13px" class="text-weight-bold">
            {{ sessao.iniciais }}
          </q-avatar>
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

    <q-drawer v-model="menuAberto" show-if-above :width="248" class="piki-menu">
      <q-list padding dark>
        <item-menu v-for="item in menu" :key="item.titulo" :item="item" />
      </q-list>
      <assinatura-piki class="piki-menu__rodape" />
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

import AssinaturaPiki from '@/componentes/AssinaturaPiki.vue'
import ItemMenu from '@/componentes/ItemMenu.vue'
import MarcaLoja from '@/componentes/MarcaLoja.vue'
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
