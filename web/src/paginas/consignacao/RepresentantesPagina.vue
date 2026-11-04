<template>
  <!-- os representantes do consignado (D30): clientes que levam mercadoria da loja -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <div class="piki-titulo col">Representantes</div>
      <q-btn v-if="sessao.pode('representantes.editar')" color="primary" unelevated no-caps icon="add" label="Novo representante" @click="novo" />
    </div>

    <q-table
      flat
      bordered
      :rows="representantes"
      :columns="colunas"
      row-key="id"
      :loading="carregando"
      :pagination="{ rowsPerPage: 30 }"
      no-data-label="Nenhum representante encontrado"
      class="tabela-clicavel"
      @row-click="(_, r) => $router.push({ name: 'representante', params: { id: r.id } })"
    >
      <template #top>
        <div class="row items-center q-gutter-md full-width">
          <q-input v-model="busca" dense outlined placeholder="Nome, CPF ou código" clearable debounce="300" class="col-12 col-sm" @update:model-value="buscar">
            <template #prepend><q-icon name="search" /></template>
          </q-input>
          <q-toggle v-model="soAtivos" label="Só ativos" @update:model-value="buscar" />
        </div>
      </template>
      <template #body-cell-situacao="props">
        <q-td :props="props">
          <q-badge v-if="!props.row.ativo" color="grey">Inativo</q-badge>
          <q-badge v-else :color="props.row.bloqueado ? 'negative' : 'positive'">{{ props.row.bloqueado ? 'Bloqueado' : 'Liberado' }}</q-badge>
        </q-td>
      </template>
    </q-table>

    <!-- o representante é um cliente especializado: escolhe o cliente (ou cadastra antes, na tela de clientes) -->
    <q-dialog v-model="dialogo">
      <q-card class="cartao-estreito">
        <q-card-section class="piki-titulo">Novo representante</q-card-section>
        <q-card-section class="q-pt-none q-gutter-sm">
          <div class="text-caption text-suave">
            O representante é um cliente: os dados pessoais, o endereço e os telefones ficam na ficha do cliente. Se ele ainda não é cliente, cadastre-o antes.
          </div>
          <q-select
            v-model="clienteId"
            outlined
            use-input
            input-debounce="300"
            label="Cliente (nome ou CPF)"
            :options="clientes"
            option-value="id"
            :option-label="(c) => (c.cpf_cnpj ? `${c.nome} · ${formatarDocumento(c.cpf_cnpj)}` : c.nome)"
            emit-value
            map-options
            @filter="buscarClientes"
          >
            <template #no-option><q-item><q-item-section class="text-suave">Digite ao menos duas letras</q-item-section></q-item></template>
          </q-select>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn v-close-popup flat no-caps label="Cancelar" />
          <q-btn unelevated no-caps color="primary" label="Criar" :disable="!clienteId" :loading="criando" @click="criar" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDocumento, formatarMoeda, nomeSetor } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const roteador = useRouter()
const sessao = useSessaoStore()
const representantes = ref([])
const carregando = ref(true)
const busca = ref('')
const soAtivos = ref(true)
const dialogo = ref(false)
const clientes = ref([])
const clienteId = ref(null)
const criando = ref(false)

const colunas = [
  { name: 'codigo', label: 'Código', field: 'codigo', align: 'left' },
  { name: 'nome', label: 'Nome', field: (r) => r.cliente.nome, align: 'left' },
  { name: 'cpf', label: 'CPF', field: (r) => (r.cliente.cpf_cnpj ? formatarDocumento(r.cliente.cpf_cnpj) : ''), align: 'left' },
  { name: 'setor', label: 'Setor', field: (r) => (r.cliente.setor ? nomeSetor(r.cliente.setor) : ''), align: 'left' },
  { name: 'limite', label: 'Limite', field: 'limite', format: formatarMoeda, align: 'right' },
  { name: 'situacao', label: 'Situação', field: 'ativo', align: 'left' },
]

async function buscar() {
  carregando.value = true
  try {
    representantes.value = (await api.get('/representantes', { params: { busca: busca.value || null, so_ativos: soAtivos.value } })).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

function novo() {
  clienteId.value = null
  dialogo.value = true
}

function buscarClientes(texto, atualizar, cancelar) {
  if (texto.trim().length < 2) return cancelar()
  api
    .get('/clientes', { params: { busca: texto.trim(), limite: 20 } })
    .then(({ data }) => atualizar(() => (clientes.value = data.itens)))
    .catch(() => cancelar())
}

async function criar() {
  criando.value = true
  try {
    const { data } = await api.post('/representantes', { cliente_id: clienteId.value })
    roteador.push({ name: 'representante', params: { id: data.id } })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    criando.value = false
  }
}

onMounted(buscar)
</script>
