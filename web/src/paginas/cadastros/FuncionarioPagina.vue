<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'funcionarios' }" />
      <div class="piki-titulo col">{{ novo ? 'Novo funcionário' : form.nome || 'Funcionário' }}</div>
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>

    <q-form v-else ref="formulario" class="formulario" @submit.prevent="salvar">
      <fieldset :disabled="!podeEditar" class="sem-borda">
        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Identificação</div>
          <div class="row q-col-gutter-md">
            <q-input
              v-model="form.nome"
              outlined
              label="Nome completo *"
              maxlength="80"
              class="col-12 col-md-6"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            />
            <q-input v-model="form.apelido" outlined label="Apelido" hint="Como é chamado na loja" maxlength="30" class="col-12 col-sm-6 col-md-3" />
            <q-input
              v-model="form.cpf"
              outlined
              label="CPF"
              mask="###.###.###-##"
              unmasked-value
              class="col-12 col-sm-6 col-md-3"
              :rules="[(v) => !v || v.length === 11 || 'CPF incompleto']"
            />
            <q-input v-model="form.rg" outlined label="RG" maxlength="20" class="col-12 col-sm-6 col-md-3" />
            <q-input v-model="form.data_nascimento" outlined label="Nascimento" type="date" stack-label class="col-12 col-sm-6 col-md-3" />
            <q-select
              v-model="form.sexo"
              outlined
              label="Sexo"
              :options="[{ value: 'F', label: 'Feminino' }, { value: 'M', label: 'Masculino' }]"
              emit-value
              map-options
              clearable
              class="col-12 col-sm-6 col-md-3"
            />
            <q-input v-model="form.naturalidade" outlined label="Naturalidade" maxlength="40" class="col-12 col-sm-6 col-md-3" />
          </div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Trabalho</div>
          <div class="row q-col-gutter-md items-start">
            <q-select
              v-model="form.empresa_id"
              outlined
              label="Loja *"
              :options="lojas"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              class="col-12 col-sm-6 col-md-4"
              :rules="[(v) => !!v || 'Escolha a loja']"
            >
              <template #option="{ itemProps, opt }">
                <q-item v-bind="itemProps">
                  <q-item-section avatar>
                    <q-avatar text-color="white" size="24px" font-size="11px" :style="{ background: opt.cor }">{{ opt.codigo }}</q-avatar>
                  </q-item-section>
                  <q-item-section>{{ opt.nome }}</q-item-section>
                </q-item>
              </template>
            </q-select>
            <q-select
              v-model="form.cargo_id"
              outlined
              label="Cargo"
              :options="cargos"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              clearable
              class="col-12 col-sm-6 col-md-4"
            />
            <q-input
              v-model.number="form.limite_vale"
              outlined
              label="Limite para vales"
              type="number"
              min="0"
              step="0.01"
              prefix="R$"
              class="col-12 col-sm-6 col-md-4"
            />
            <div class="col-12 row q-gutter-lg">
              <q-toggle v-model="form.ativo" label="Ativo" />
              <q-toggle v-model="form.pode_tirar_vale" label="Pode tirar vale" />
            </div>
          </div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Telefones</div>
          <div v-for="(tel, i) in form.telefones" :key="i" class="row q-col-gutter-md items-start q-mb-sm">
            <q-input
              v-model="tel.numero"
              outlined
              label="Número com DDD"
              :mask="mascaraTelefone(tel.numero)"
              unmasked-value
              class="col-12 col-sm-5"
              :rules="[(v) => soDigitos(v).length >= 10 || 'Número incompleto']"
            />
            <q-select
              v-model="tel.tipo"
              outlined
              label="Tipo"
              :options="TIPOS_TELEFONE"
              emit-value
              map-options
              class="col-10 col-sm-4"
            />
            <div class="col-2 col-sm-auto">
              <q-btn flat round icon="delete_outline" color="grey-7" aria-label="Remover telefone" @click="form.telefones.splice(i, 1)" />
            </div>
          </div>
          <q-btn flat no-caps color="primary" icon="add" label="Adicionar telefone" @click="form.telefones.push({ numero: '', tipo: '3' })" />
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Endereço</div>
          <div class="row q-col-gutter-md">
            <q-input v-model="form.cep" outlined label="CEP" mask="#####-###" unmasked-value class="col-12 col-sm-4 col-md-2" />
            <q-input v-model="form.logradouro" outlined label="Endereço" maxlength="60" class="col-12 col-sm-8 col-md-5" />
            <selecao-busca
              v-model="form.setor_id"
              :opcoes="setores"
              :rotulo="nomeSetor"
              label="Setor"
              hint="Bairro; a cidade é a do setor"
              class="col-12 col-md-5"
            />
          </div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Família e observações</div>
          <div class="row q-col-gutter-md">
            <q-input v-model="form.conjuge" outlined label="Cônjuge" maxlength="60" class="col-12 col-md-4" />
            <q-input v-model="form.pai" outlined label="Pai" maxlength="60" class="col-12 col-sm-6 col-md-4" />
            <q-input v-model="form.mae" outlined label="Mãe" maxlength="60" class="col-12 col-sm-6 col-md-4" />
            <q-input v-model="form.endereco_pais" outlined label="Endereço dos pais" maxlength="100" class="col-12" />
            <q-input v-model="form.observacao" outlined label="Observações" type="textarea" autogrow maxlength="2000" class="col-12" />
          </div>
        </section>
      </fieldset>

      <div v-if="podeEditar" class="formulario__acoes row justify-end q-gutter-sm">
        <q-btn flat no-caps label="Cancelar" :to="{ name: 'funcionarios' }" />
        <q-btn type="submit" color="primary" unelevated no-caps icon="check" label="Salvar" :loading="salvando" />
      </div>
    </q-form>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { mascaraTelefone, soDigitos, TIPOS_TELEFONE } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()

const novo = computed(() => !rota.params.id)
const podeEditar = computed(() => sessao.pode('funcionarios.editar'))

const carregando = ref(true)
const salvando = ref(false)
const cargos = ref([])
const setores = ref([])
const empresaAtual = ref(null)

function vazio() {
  return {
    nome: '', apelido: '', cpf: '', rg: '', data_nascimento: null, sexo: null, naturalidade: '',
    empresa_id: sessao.empresa?.id ?? null, cargo_id: null, ativo: true, pode_tirar_vale: true, limite_vale: 0,
    cep: '', logradouro: '', setor_id: null,
    conjuge: '', pai: '', mae: '', endereco_pais: '', observacao: '',
    telefones: [],
  }
}
const form = ref(vazio())

function nomeSetor(s) {
  return s ? (s.cidade ? `${s.nome} (${s.cidade.nome} - ${s.cidade.uf})` : s.nome) : ''
}

// lojas do usuário; a do funcionário entra mesmo que o usuário não tenha acesso a ela
const lojas = computed(() => {
  const lista = [...sessao.empresas]
  if (empresaAtual.value && !lista.some((e) => e.id === empresaAtual.value.id)) lista.push(empresaAtual.value)
  return lista
})

onMounted(async () => {
  try {
    // a lista de setores é de clientes; quem edita funcionários também pode lê-la
    const pedidos = [
      api.get('/cargos'),
      sessao.pode('clientes.ver') || podeEditar.value ? api.get('/setores') : { data: [] },
    ]
    if (!novo.value) pedidos.push(api.get(`/funcionarios/${rota.params.id}`))
    const [respCargos, respSetores, respFuncionario] = await Promise.all(pedidos)
    cargos.value = respCargos.data.filter((c) => c.ativo || c.id === respFuncionario?.data.cargo_id)
    setores.value = respSetores.data
    if (respFuncionario) {
      const { id, empresa, cargo, setor, ...dados } = respFuncionario.data
      // sem a lista (só consulta), o setor atual basta para mostrar o nome
      if (setor && !setores.value.some((s) => s.id === setor.id)) setores.value = [setor, ...setores.value]
      empresaAtual.value = empresa
      form.value = { ...vazio(), ...dados, limite_vale: Number(dados.limite_vale) }
    }
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

async function salvar() {
  salvando.value = true
  try {
    const dados = { ...form.value, limite_vale: (Number(form.value.limite_vale) || 0).toFixed(2) }
    const resp = novo.value
      ? await api.post('/funcionarios', dados)
      : await api.put(`/funcionarios/${rota.params.id}`, dados)
    $q.notify({ type: 'positive', message: 'Funcionário salvo', timeout: 1500 })
    if (novo.value) await roteador.replace({ name: 'funcionario', params: { id: resp.data.id } })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}
</script>
