<template>
  <q-layout>
    <q-page-container>
      <q-page class="login">
        <!-- painel da loja, só em telas largas -->
        <section class="login__marca column justify-between gt-sm">
          <marca-loja :tamanho="48" clara />
          <div>
            <div class="login__titulo q-mb-lg">Gestão comercial de todas as lojas, num lugar só.</div>
            <div v-for="r in recursos" :key="r.texto" class="login__recurso row items-center no-wrap q-mb-sm">
              <q-icon :name="r.icone" size="20px" class="q-mr-sm" />{{ r.texto }}
            </div>
          </div>
          <assinatura-piki />
        </section>

        <section class="login__formulario">
          <div class="cartao-estreito">
            <marca-loja :tamanho="44" class="lt-md q-mb-xl" />
            <div class="piki-titulo q-mb-xs">Entrar</div>
            <div class="text-suave q-mb-lg">Use seu usuário e senha.</div>

            <q-form @submit.prevent="entrar">
              <div class="q-gutter-md">
                <q-input
                  v-model.trim="login"
                  outlined
                  label="Usuário"
                  autofocus
                  autocomplete="username"
                  :rules="[(v) => !!v || 'Informe o usuário']"
                  lazy-rules
                >
                  <template #prepend><q-icon name="person" /></template>
                </q-input>
                <q-input
                  v-model="senha"
                  outlined
                  label="Senha"
                  :type="mostrarSenha ? 'text' : 'password'"
                  autocomplete="current-password"
                  :rules="[(v) => !!v || 'Informe a senha']"
                  lazy-rules
                >
                  <template #prepend><q-icon name="lock" /></template>
                  <template #append>
                    <q-icon
                      :name="mostrarSenha ? 'visibility_off' : 'visibility'"
                      class="cursor-pointer"
                      :aria-label="mostrarSenha ? 'Esconder senha' : 'Mostrar senha'"
                      @click="mostrarSenha = !mostrarSenha"
                    />
                  </template>
                </q-input>
                <q-banner v-if="erro" class="bg-red-1 text-negative" rounded dense>
                  <template #avatar><q-icon name="error_outline" /></template>
                  {{ erro }}
                </q-banner>
              </div>

              <q-btn
                type="submit"
                color="primary"
                label="Entrar"
                size="lg"
                no-caps
                unelevated
                class="full-width q-mt-lg"
                :loading="enviando"
              />
            </q-form>
          </div>
        </section>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import MarcaLoja from '@/componentes/MarcaLoja.vue'
import AssinaturaPiki from '@/componentes/AssinaturaPiki.vue'
import { mensagemDeErro } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const sessao = useSessaoStore()
const roteador = useRouter()
const rota = useRoute()

const login = ref('')
const senha = ref('')
const mostrarSenha = ref(false)
const enviando = ref(false)
const erro = ref('')

const recursos = [
  { icone: 'point_of_sale', texto: 'PDV, caixa e financeiro' },
  { icone: 'inventory_2', texto: 'Estoque e consignação por loja' },
  { icone: 'receipt_long', texto: 'NF-e, NFC-e e SPED' },
]

async function entrar() {
  erro.value = ''
  enviando.value = true
  try {
    const resposta = await sessao.entrar(login.value, senha.value)
    if (!resposta.empresa) {
      await roteador.push({ name: 'escolher-empresa', query: rota.query })
    } else {
      await roteador.push(rota.query.volta || '/')
    }
  } catch (e) {
    erro.value = mensagemDeErro(e)
    senha.value = ''
  } finally {
    enviando.value = false
  }
}
</script>
