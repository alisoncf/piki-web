<template>
  <q-layout>
    <q-page-container>
      <q-page class="pagina-centralizada">
        <q-card class="cartao-estreito" flat bordered>
          <q-card-section class="text-center q-pt-lg">
            <div class="text-h4 text-primary text-weight-bold">Piki</div>
            <div class="text-subtitle2 text-grey-7">Entre com seu usuário e senha</div>
          </q-card-section>

          <q-form @submit.prevent="entrar">
            <q-card-section class="q-gutter-md">
              <q-input
                v-model.trim="login"
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
            </q-card-section>

            <q-card-actions class="q-px-md q-pb-lg">
              <q-btn type="submit" color="primary" label="Entrar" class="full-width" unelevated :loading="enviando" />
            </q-card-actions>
          </q-form>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

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
