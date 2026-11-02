<template>
  <!-- login e senha de quem autoriza o que passou do limite (desconto, parcelas, crediário); ver usarAutorizacao -->
  <q-dialog :model-value="estado.aberto" @hide="emit('responder', null)">
    <q-card class="cartao-estreito">
      <q-form @submit.prevent="emit('responder', { login: estado.login, senha: estado.senha })">
        <q-card-section class="piki-titulo">Autorização</q-card-section>
        <q-card-section class="q-gutter-sm q-pt-none">
          <div>{{ estado.mensagem }}</div>
          <q-input v-model="estado.login" outlined autofocus label="Login de quem autoriza" autocomplete="off" />
          <q-input v-model="estado.senha" outlined type="password" label="Senha" autocomplete="new-password" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat no-caps label="Cancelar" @click="emit('responder', null)" />
          <q-btn type="submit" color="primary" unelevated no-caps label="Autorizar" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
defineProps({ estado: { type: Object, required: true } })
const emit = defineEmits(['responder'])
</script>
