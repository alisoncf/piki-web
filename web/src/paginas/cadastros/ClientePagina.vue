<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'clientes' }" />
      <div class="piki-titulo col">{{ novo ? 'Novo cliente' : form.nome || 'Cliente' }}</div>
      <q-badge v-if="!novo && form.bloqueado" color="negative" class="q-mr-xs">Bloqueado</q-badge>
      <q-badge v-if="!novo && form.credito_suspenso" color="warning" text-color="dark">Crédito suspenso</q-badge>
    </div>
    <div v-if="!novo && info" class="text-caption text-suave q-mb-md">
      Cliente desde {{ formatarDataHora(info.data_cadastro) }}<template v-if="info.empresa_cadastro">, em {{ info.empresa_cadastro.nome }}</template>
      <template v-if="info.data_alteracao"> · alterado em {{ formatarDataHora(info.data_alteracao) }}</template>
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>

    <q-form v-else ref="formulario" class="formulario" @submit.prevent="salvar">
      <fieldset :disabled="!podeEditar" class="sem-borda">
        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Identificação</div>
          <div class="row q-col-gutter-md">
            <q-btn-toggle
              v-model="form.tipo"
              no-caps
              unelevated
              toggle-color="primary"
              :options="[{ value: 'F', label: 'Pessoa física' }, { value: 'J', label: 'Pessoa jurídica' }]"
              class="col-12"
              @update:model-value="form.cpf_cnpj = ''"
            />
            <q-input
              v-model="form.nome"
              outlined
              :label="form.tipo === 'J' ? 'Razão social *' : 'Nome completo *'"
              maxlength="60"
              class="col-12 col-md-6"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            />
            <q-input
              v-model="form.cpf_cnpj"
              outlined
              :label="form.tipo === 'J' ? 'CNPJ' : 'CPF'"
              :mask="form.tipo === 'J' ? '##.###.###/####-##' : '###.###.###-##'"
              unmasked-value
              class="col-12 col-sm-6 col-md-3"
              :rules="[(v) => !v || v.length === (form.tipo === 'J' ? 14 : 11) || 'Documento incompleto']"
            />
            <q-input
              v-if="form.tipo === 'F'"
              v-model="form.rg"
              outlined
              label="RG"
              maxlength="20"
              class="col-12 col-sm-6 col-md-3"
            />
            <q-input v-else v-model="form.inscricao_estadual" outlined label="Inscrição estadual" maxlength="20" class="col-12 col-sm-6 col-md-3" />
            <template v-if="form.tipo === 'F'">
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
              <q-input v-model="form.pai" outlined label="Pai" maxlength="60" class="col-12 col-sm-6 col-md-3" />
              <q-input v-model="form.mae" outlined label="Mãe" maxlength="60" class="col-12 col-sm-6 col-md-3" />
            </template>
            <q-input v-model="form.email" outlined label="E-mail" type="email" maxlength="100" class="col-12 col-md-6" />
          </div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Telefones</div>
          <div v-for="(tel, i) in form.telefones" :key="i" class="row q-col-gutter-md items-start q-mb-sm">
            <q-input
              v-model="tel.numero"
              outlined
              label="Número"
              :mask="mascaraTelefone(tel.numero)"
              unmasked-value
              class="col-12 col-sm-5"
              :rules="[(v) => soDigitos(v).length >= 8 || 'Número incompleto']"
            />
            <q-select v-model="tel.tipo" outlined label="Tipo" :options="TIPOS_TELEFONE" emit-value map-options class="col-10 col-sm-4" />
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
            <q-input v-model="form.logradouro" outlined label="Logradouro" maxlength="100" class="col-12 col-sm-8 col-md-6" />
            <q-input v-model="form.numero" outlined label="Número" maxlength="20" class="col-6 col-sm-4 col-md-2" />
            <q-input v-model="form.complemento" outlined label="Complemento" maxlength="60" class="col-6 col-sm-8 col-md-2" />
            <q-input v-model="form.bairro" outlined label="Bairro" maxlength="40" class="col-12 col-sm-6 col-md-3" />
            <q-input v-model="form.cidade" outlined label="Cidade" maxlength="40" class="col-9 col-sm-4 col-md-3" />
            <q-input v-model="form.uf" outlined label="UF" mask="AA" class="col-3 col-sm-2 col-md-1" @update:model-value="(v) => (form.uf = v?.toUpperCase())" />
            <q-input v-model="form.ponto_referencia" outlined label="Ponto de referência" maxlength="60" class="col-12 col-md-5" />
            <selecao-busca
              v-model="form.setor_id"
              :opcoes="setores"
              :rotulo="nomeSetor"
              label="Setor de cobrança"
              hint="Bairro ou região do cobrador"
              class="col-12 col-md-6"
            />
          </div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Trabalho</div>
          <div class="row q-col-gutter-md">
            <selecao-busca v-model="form.orgao_id" :opcoes="orgaos" label="Órgão / empresa" class="col-12 col-md-6" />
            <q-select
              v-model="form.grupo_id"
              outlined
              label="Grupo"
              :options="grupos"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              clearable
              class="col-12 col-sm-6 col-md-3"
            />
            <q-input v-model="form.local_trabalho" outlined label="Local / função" maxlength="60" class="col-12 col-sm-6 col-md-3" />
            <q-input v-model="form.endereco_trabalho" outlined label="Endereço do trabalho" maxlength="60" class="col-12 col-md-6" />
            <q-input
              v-model="form.telefone_trabalho"
              outlined
              label="Telefone do trabalho"
              :mask="mascaraTelefone(form.telefone_trabalho)"
              unmasked-value
              class="col-12 col-sm-6 col-md-3"
            />
            <q-input v-model="form.cep_trabalho" outlined label="CEP do trabalho" mask="#####-###" unmasked-value class="col-12 col-sm-6 col-md-3" />
            <selecao-busca
              v-model="form.setor_trabalho_id"
              :opcoes="setores"
              :rotulo="nomeSetor"
              label="Setor do trabalho"
              hint="Usado na cobrança no trabalho"
              class="col-12 col-md-6"
            />
          </div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Crédito e cobrança</div>
          <div class="row q-col-gutter-md items-start">
            <q-input
              v-model.number="form.limite_credito"
              outlined
              label="Limite de crédito"
              type="number"
              min="0"
              step="0.01"
              prefix="R$"
              class="col-12 col-sm-6 col-md-3"
            />
            <q-select
              v-model="form.forma_cobranca"
              outlined
              label="Cobrança"
              :options="FORMAS_COBRANCA"
              emit-value
              map-options
              class="col-12 col-sm-6 col-md-3"
            />
            <div class="col-12 row q-gutter-lg">
              <q-toggle v-model="form.bloqueado" color="negative" label="Bloqueado (não compra a prazo)" />
              <q-toggle v-model="form.credito_suspenso" color="warning" label="Crédito suspenso" />
              <q-toggle v-model="form.recebe_mensagens" label="Recebe mensagens" />
              <q-toggle v-model="form.especial" label="Cliente especial" />
            </div>
          </div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Referências</div>
          <div v-for="(ref_, i) in form.referencias" :key="i" class="row q-col-gutter-md items-start q-mb-sm">
            <q-input
              v-model="ref_.nome"
              outlined
              label="Nome"
              maxlength="60"
              class="col-12 col-sm-5"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            />
            <q-input v-model="ref_.telefone" outlined label="Telefone" :mask="mascaraTelefone(ref_.telefone)" unmasked-value class="col-6 col-sm-3" />
            <q-select
              v-model="ref_.parentesco_id"
              outlined
              label="Parentesco"
              :options="parentescos"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              clearable
              class="col-4 col-sm-3"
            />
            <div class="col-2 col-sm-auto">
              <q-btn flat round icon="delete_outline" color="grey-7" aria-label="Remover referência" @click="form.referencias.splice(i, 1)" />
            </div>
          </div>
          <q-btn
            flat
            no-caps
            color="primary"
            icon="add"
            label="Adicionar referência"
            @click="form.referencias.push({ nome: '', telefone: '', parentesco_id: null })"
          />
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Observações</div>
          <q-input v-model="form.observacao" outlined type="textarea" autogrow maxlength="4000" />
        </section>
      </fieldset>

      <div v-if="podeEditar" class="formulario__acoes row justify-end q-gutter-sm q-mb-md">
        <q-btn flat no-caps label="Cancelar" :to="{ name: 'clientes' }" />
        <q-btn type="submit" color="primary" unelevated no-caps icon="check" label="Salvar" :loading="salvando" />
      </div>

      <section v-if="!novo" class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Anotações</div>
        <div v-if="podeEditar" class="row q-col-gutter-md items-start q-mb-md">
          <q-input v-model="anotacao" outlined autogrow label="Nova anotação" maxlength="4000" class="col" />
          <div class="col-auto">
            <q-btn unelevated no-caps color="primary" label="Anotar" :disable="!anotacao.trim()" :loading="anotando" @click="anotar" />
          </div>
        </div>
        <q-list v-if="anotacoes.length" separator>
          <q-item v-for="a in anotacoes" :key="a.id" class="q-px-none">
            <q-item-section>
              <q-item-label class="anotacao">{{ a.texto }}</q-item-label>
              <q-item-label caption>
                {{ formatarDataHora(a.data_hora) }}<template v-if="a.usuario"> · {{ a.usuario.nome }}</template><template v-if="a.empresa"> · {{ a.empresa.nome }}</template>
              </q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
        <div v-else class="text-suave">Nenhuma anotação.</div>
      </section>
    </q-form>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { FORMAS_COBRANCA, formatarDataHora, mascaraTelefone, soDigitos, TIPOS_TELEFONE } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()

const novo = computed(() => !rota.params.id)
const podeEditar = computed(() => sessao.pode('clientes.editar'))

const carregando = ref(true)
const salvando = ref(false)
const setores = ref([])
const orgaos = ref([])
const grupos = ref([])
const parentescos = ref([])
const info = ref(null) // o que vem da API e não se edita: datas, loja do cadastro
const anotacoes = ref([])
const anotacao = ref('')
const anotando = ref(false)

function vazio() {
  return {
    nome: '', tipo: 'F', cpf_cnpj: '', rg: '', inscricao_estadual: '', data_nascimento: null, sexo: null,
    pai: '', mae: '', email: '',
    cep: '', logradouro: '', numero: '', complemento: '', bairro: '', ponto_referencia: '', cidade: '', uf: '',
    codigo_municipio: null, setor_id: null,
    grupo_id: null, orgao_id: null, local_trabalho: '', endereco_trabalho: '', telefone_trabalho: '', cep_trabalho: '',
    setor_trabalho_id: null,
    bloqueado: false, forma_cobranca: 'domicilio', limite_credito: 0, credito_suspenso: false,
    recebe_mensagens: true, especial: false, observacao: '',
    telefones: [], referencias: [],
  }
}
const form = ref(vazio())

function nomeSetor(s) {
  return s ? (s.cidade ? `${s.nome} (${s.cidade})` : s.nome) : ''
}

function preencher(cliente) {
  const {
    id, data_cadastro, data_alteracao, empresa_cadastro, anotacoes: lista, setor, setor_trabalho, grupo, orgao,
    referencias, ...dados
  } = cliente
  info.value = { data_cadastro, data_alteracao, empresa_cadastro }
  anotacoes.value = lista
  form.value = {
    ...vazio(),
    ...dados,
    limite_credito: Number(dados.limite_credito),
    referencias: referencias.map(({ nome, telefone, parentesco_id }) => ({ nome, telefone, parentesco_id })),
  }
}

onMounted(async () => {
  try {
    const pedidos = ['/setores', '/orgaos', '/grupos-clientes', '/parentescos'].map((url) => api.get(url))
    if (!novo.value) pedidos.push(api.get(`/clientes/${rota.params.id}`))
    const [s, o, g, p, c] = await Promise.all(pedidos)
    setores.value = s.data
    orgaos.value = o.data
    grupos.value = g.data
    parentescos.value = p.data
    if (c) preencher(c.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

async function salvar() {
  salvando.value = true
  try {
    const dados = { ...form.value, limite_credito: (Number(form.value.limite_credito) || 0).toFixed(2) }
    const resp = novo.value ? await api.post('/clientes', dados) : await api.put(`/clientes/${rota.params.id}`, dados)
    $q.notify({ type: 'positive', message: 'Cliente salvo', timeout: 1500 })
    if (novo.value) await roteador.replace({ name: 'cliente', params: { id: resp.data.id } })
    // a página continua montada depois do replace: mostra o que a API gravou
    preencher(resp.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

async function anotar() {
  anotando.value = true
  try {
    const { data } = await api.post(`/clientes/${rota.params.id}/anotacoes`, { texto: anotacao.value })
    anotacoes.value = data.anotacoes
    anotacao.value = ''
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    anotando.value = false
  }
}
</script>

<style scoped>
.anotacao {
  white-space: pre-wrap;
}
</style>
