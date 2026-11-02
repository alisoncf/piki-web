<template>
  <q-layout>
    <q-page-container>
      <q-page class="pagina-centralizada column">
        <marca-loja :tamanho="44" class="q-mb-lg" />
        <div class="cartao cartao-estreito q-pa-lg">
          <div class="piki-titulo q-mb-xs">{{ obrigatoria ? 'Crie a sua senha' : 'Trocar senha' }}</div>
          <div class="text-suave q-mb-lg">
            <template v-if="obrigatoria">A senha que você usou é provisória. Crie uma senha só sua para continuar.</template>
            <template v-else>Escolha uma senha nova.</template>
            Ela precisa ter pelo menos {{ MINIMO }} caracteres e diferencia maiúsculas de minúsculas.
          </div>

          <q-form class="q-gutter-md" @submit.prevent="salvar">
            <q-input
              v-model="atual"
              outlined
              :label="obrigatoria ? 'Senha provisória' : 'Senha atual'"
              :type="mostrar ? 'text' : 'password'"
              autocomplete="current-password"
              autofocus
              :rules="[(v) => !!v || 'Informe a senha atual']"
              lazy-rules
            />
            <q-input
              v-model="nova"
              outlined
              label="Senha nova"
              :type="mostrar ? 'text' : 'password'"
              autocomplete="new-password"
              :rules="[(v) => (v || '').length >= MINIMO || `Pelo menos ${MINIMO} caracteres`]"
              lazy-rules
            >
              <template #append>
                <q-icon
                  :name="mostrar ? 'visibility_off' : 'visibility'"
                  class="cursor-pointer"
                  :aria-label="mostrar ? 'Esconder senhas' : 'Mostrar senhas'"
                  @click="mostrar = !mostrar"
                />
              </template>
            </q-input>
            <q-input
              v-model="repetida"
              outlined
              label="Repita a senha nova"
              :type="mostrar ? 'text' : 'password'"
              autocomplete="new-password"
              :rules="[(v) => v === nova || 'As senhas não são iguais']"
              lazy-rules
            />
            <q-banner v-if="erro" class="bg-red-1 text-negative" rounded dense>
              <template #avatar><q-icon name="error_outline" /></template>
              {{ erro }}
            </q-banner>
            <div class="row justify-end q-gutter-sm">
              <q-btn v-if="obrigatoria" flat no-caps color="grey-8" label="Sair" icon="logout" @click="sair" />
              <q-btn v-else flat no-caps label="Cancelar" @click="voltar" />
              <q-btn type="submit" color="primary" unelevated no-caps icon="check" label="Salvar senha" :loading="enviando" />
            </div>
          </q-form>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import MarcaLoja from '@/componentes/MarcaLoja.vue'
import { mensagemDeErro } from '@/servicos/api'
import { useSessaoStore } from '@/stores/sessao'

const MINIMO = 8 // o mesmo da API (SENHA_MINIMA em app/dominios/acesso/servico.py)

const $q = useQuasar()
const sessao = useSessaoStore()
const roteador = useRouter()
const rota = useRoute()

// obrigatória: senha provisória; senão, veio pelo menu do usuário
const obrigatoria = sessao.precisaTrocarSenha
const atual = ref('')
const nova = ref('')
const repetida = ref('')
const mostrar = ref(false)
const enviando = ref(false)
const erro = ref('')

function voltar() {
  roteador.push(rota.query.volta || '/')
}

async function salvar() {
  enviando.value = true
  erro.value = ''
  try {
    await sessao.trocarSenha(atual.value, nova.value)
    $q.notify({ type: 'positive', message: 'Senha trocada', timeout: 1500 })
    voltar()
  } catch (e) {
    erro.value = mensagemDeErro(e)
  } finally {
    enviando.value = false
  }
}

function sair() {
  sessao.sair()
  roteador.push({ name: 'login' })
}
</script>
