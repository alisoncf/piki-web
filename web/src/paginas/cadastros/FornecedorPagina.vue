<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'fornecedores' }" />
      <div class="piki-titulo col">{{ novo ? 'Novo fornecedor' : form.nome || 'Fornecedor' }}</div>
      <q-badge v-if="!novo && !form.ativo" color="grey-6">Inativo</q-badge>
    </div>

    <indice-ficha v-if="!carregando" :secoes="SECOES" />
    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>

    <q-form v-else class="formulario" @submit.prevent="salvar">
      <fieldset :disabled="!podeEditar" class="sem-borda">
        <section id="secao-identificacao" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Identificação</div>
          <div class="row q-col-gutter-md">
            <q-input
              v-model="documento"
              outlined
              label="CNPJ ou CPF *"
              inputmode="numeric"
              maxlength="18"
              :hint="pessoaFisica ? 'Pessoa física' : 'Com o CNPJ completo, a lupa busca os dados na Receita'"
              :rules="[(v) => [11, 14].includes(soDigitos(v).length) || 'Informe o CNPJ ou o CPF']"
              class="col-12 col-sm-6 col-md-4"
              @keydown.enter.prevent="buscarCnpj"
            >
              <template #append>
                <q-btn
                  flat
                  round
                  dense
                  icon="search"
                  :loading="buscandoCnpj"
                  :disable="soDigitos(form.cpf_cnpj).length !== 14 || !podeEditar"
                  aria-label="Buscar os dados do CNPJ na Receita"
                  @click="buscarCnpj"
                >
                  <q-tooltip>Buscar os dados do CNPJ na Receita</q-tooltip>
                </q-btn>
              </template>
            </q-input>
            <q-input
              v-model="form.nome"
              outlined
              :label="pessoaFisica ? 'Nome completo *' : 'Razão social *'"
              maxlength="100"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
              class="col-12 col-md-8"
            />
            <q-input v-model="form.nome_fantasia" outlined label="Nome fantasia" maxlength="60" class="col-12 col-md-6" />
            <q-input v-model="form.inscricao_estadual" outlined label="Inscrição estadual" maxlength="20" class="col-12 col-sm-6 col-md-3" />
            <q-toggle v-model="form.ativo" label="Ativo" class="col-12 col-sm-6 col-md-3" />
          </div>
        </section>

        <section id="secao-endereco" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Endereço</div>
          <div class="row q-col-gutter-md">
            <campo-cep v-model="form.cep" label="CEP" :buscando="buscandoCep" class="col-12 col-sm-4 col-md-2" @buscar="buscarCep" />
            <q-input v-model="form.logradouro" outlined label="Logradouro" maxlength="60" class="col-12 col-sm-8 col-md-6" />
            <q-input v-model="form.numero" outlined label="Número" maxlength="10" class="col-6 col-sm-4 col-md-2" />
            <q-input v-model="form.complemento" outlined label="Complemento" maxlength="60" class="col-6 col-sm-8 col-md-2" />
            <q-input v-model="form.bairro" outlined label="Bairro" maxlength="60" class="col-12 col-sm-6" />
            <selecao-cidade v-model="form.cidade_id" v-model:cidade="cidade" class="col-12 col-sm-6" />
          </div>
        </section>

        <section id="secao-telefones" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Telefones e internet</div>
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
          <q-btn flat no-caps color="primary" icon="add" label="Adicionar telefone" class="q-mb-md" @click="form.telefones.push({ numero: '', tipo: '2' })" />
          <div class="row q-col-gutter-md">
            <q-input v-model="form.email" outlined label="E-mail" type="email" maxlength="200" class="col-12 col-md-6" />
            <q-input v-model="form.site" outlined label="Site" maxlength="200" class="col-12 col-md-6" />
          </div>
        </section>

        <section id="secao-contatos" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Contatos</div>
          <div class="text-caption text-suave q-mb-md">As pessoas com quem a loja fala: representante, financeiro, vendas...</div>
          <div v-for="(c, i) in form.contatos" :key="i" class="row q-col-gutter-md items-start q-mb-sm contato">
            <q-input
              v-model="c.nome"
              outlined
              label="Nome *"
              maxlength="60"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
              class="col-12 col-sm-6 col-md-3"
            />
            <q-input v-model="c.funcao" outlined label="Função" maxlength="40" class="col-12 col-sm-6 col-md-2" />
            <q-input
              v-model="c.telefone"
              outlined
              label="Telefone"
              :mask="mascaraTelefone(c.telefone)"
              unmasked-value
              :rules="[(v) => !v || soDigitos(v).length >= 8 || 'Número incompleto']"
              class="col-12 col-sm-6 col-md-3"
            />
            <q-input v-model="c.email" outlined label="E-mail" type="email" maxlength="200" class="col-10 col-sm-5 col-md-3" />
            <div class="col-2 col-sm-1">
              <q-btn flat round icon="delete_outline" color="grey-7" aria-label="Remover contato" @click="form.contatos.splice(i, 1)" />
            </div>
          </div>
          <q-btn
            flat
            no-caps
            color="primary"
            icon="person_add"
            label="Adicionar contato"
            @click="form.contatos.push({ nome: '', funcao: '', telefone: '', email: '' })"
          />
        </section>

        <section id="secao-observacoes" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Observações</div>
          <q-input v-model="form.observacao" outlined type="textarea" autogrow maxlength="4000" />
        </section>
      </fieldset>

      <div v-if="podeEditar" class="formulario__acoes row justify-end q-gutter-sm q-mb-md">
        <q-btn flat no-caps label="Cancelar" :to="{ name: 'fornecedores' }" />
        <q-btn type="submit" color="primary" unelevated no-caps icon="check" label="Salvar" :loading="salvando" />
      </div>
    </q-form>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import CampoCep from '@/componentes/CampoCep.vue'
import IndiceFicha from '@/componentes/IndiceFicha.vue'
import SelecaoCidade from '@/componentes/SelecaoCidade.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { usarCep } from '@/servicos/cep'
import { formatarDocumento, mascaraTelefone, soDigitos, TIPOS_TELEFONE } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

// a ficha é uma página só (sem abas); o índice leva a cada parte
const SECOES = [
  ['identificacao', 'Identificação'], ['endereco', 'Endereço'], ['telefones', 'Telefones e internet'],
  ['contatos', 'Contatos'], ['observacoes', 'Observações'],
].map(([id, titulo]) => ({ id: `secao-${id}`, titulo }))

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()

const novo = computed(() => !rota.params.id)
const podeEditar = computed(() => sessao.pode('fornecedores.editar'))
const carregando = ref(true)
const salvando = ref(false)
const buscandoCnpj = ref(false)
const cidade = ref(null) // { id, nome, uf }, para o campo mostrar o nome

function vazio() {
  return {
    nome: '', nome_fantasia: '', cpf_cnpj: '', inscricao_estadual: '',
    cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade_id: null,
    email: '', site: '', observacao: '', ativo: true, telefones: [], contatos: [],
  }
}
const form = ref(vazio())

const pessoaFisica = computed(() => soDigitos(form.value.cpf_cnpj).length === 11)
// sem máscara do Quasar, que cortaria um CNPJ colado enquanto a máscara ainda é a do CPF:
// guarda só os dígitos e mostra formatado quando o número está completo
const documento = computed({
  get: () => {
    const d = soDigitos(form.value.cpf_cnpj)
    return [11, 14].includes(d.length) ? formatarDocumento(d) : d
  },
  set: (valor) => {
    form.value.cpf_cnpj = soDigitos(valor).slice(0, 14)
  },
})

const { buscando: buscandoCep, buscar: buscarCep } = usarCep(
  form, { cep: 'cep', rua: 'logradouro', bairro: 'bairro', cidade: 'cidade_id' }, { cidade },
)

function preencher(fornecedor) {
  const { id, tipo, cidade: cid, criado_em, atualizado_em, ...dados } = fornecedor
  cidade.value = cid
  form.value = { ...vazio(), ...dados }
}

async function carregar() {
  carregando.value = true
  try {
    if (!novo.value) preencher((await api.get(`/fornecedores/${rota.params.id}`)).data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
}

onMounted(carregar)

function perguntar(opcoes) {
  return new Promise((resolve) => {
    $q.dialog({ persistent: true, cancel: { flat: true, label: 'Não' }, ok: { label: 'Sim' }, ...opcoes })
      .onOk(() => resolve(true))
      .onCancel(() => resolve(false))
  })
}

// campos da ficha que a Receita preenche
const DA_RECEITA = {
  nome: 'razao_social', nome_fantasia: 'nome_fantasia', cep: 'cep', logradouro: 'logradouro', numero: 'numero',
  complemento: 'complemento', bairro: 'bairro', email: 'email',
}

async function buscarCnpj() {
  const cnpj = soDigitos(form.value.cpf_cnpj)
  if (cnpj.length !== 14 || buscandoCnpj.value) return
  buscandoCnpj.value = true
  let dados
  try {
    dados = (await api.get(`/cnpj/${cnpj}`)).data
  } catch (e) {
    $q.notify({ type: e.response?.status === 503 ? 'warning' : 'negative', message: mensagemDeErro(e) })
    return
  } finally {
    buscandoCnpj.value = false
  }

  if (dados.fornecedor_id && String(dados.fornecedor_id) !== String(rota.params.id ?? '')) {
    if (await perguntar({ title: 'Fornecedor já cadastrado', message: `${dados.razao_social ?? 'Este CNPJ'} já está cadastrado. Abrir a ficha dele?` })) {
      // a mesma página continua montada: carrega a outra ficha
      await roteador.push({ name: 'fornecedor', params: { id: dados.fornecedor_id } })
      await carregar()
    }
    return
  }
  if (dados.situacao && dados.situacao !== 'ATIVA') {
    $q.notify({ type: 'warning', message: `Na Receita, a situação deste CNPJ é ${dados.situacao}.`, timeout: 6000 })
  }

  // o que já estava preenchido só é trocado se a pessoa confirmar
  const atual = form.value
  const diferentes = Object.entries(DA_RECEITA).filter(([campo, da]) => dados[da] && atual[campo]?.trim() && atual[campo].trim() !== dados[da])
  const outraCidade = dados.cidade && atual.cidade_id && atual.cidade_id !== dados.cidade.id
  const trocar = (diferentes.length || outraCidade)
    ? await perguntar({ title: 'Dados da Receita', message: 'Trocar o que já está preenchido pelos dados da Receita? Com "Não", só os campos vazios são preenchidos.' })
    : true
  for (const [campo, da] of Object.entries(DA_RECEITA)) {
    if (dados[da] && (trocar || !atual[campo]?.trim())) atual[campo] = dados[da]
  }
  if (dados.cidade && (trocar || !atual.cidade_id)) {
    cidade.value = dados.cidade
    atual.cidade_id = dados.cidade.id
  }
  const numeros = new Set(atual.telefones.map((t) => soDigitos(t.numero)))
  for (const numero of dados.telefones) {
    if (!numeros.has(numero)) atual.telefones.push({ numero, tipo: '2' })
  }
  $q.notify({ type: 'positive', message: 'Dados da Receita preenchidos; confira e salve', timeout: 2000 })
}

async function salvar() {
  salvando.value = true
  try {
    const dados = { ...form.value, cpf_cnpj: soDigitos(form.value.cpf_cnpj) }
    const resp = novo.value ? await api.post('/fornecedores', dados) : await api.put(`/fornecedores/${rota.params.id}`, dados)
    $q.notify({ type: 'positive', message: 'Fornecedor salvo', timeout: 1500 })
    if (novo.value) await roteador.replace({ name: 'fornecedor', params: { id: resp.data.id } })
    // a página continua montada depois do replace: mostra o que a API gravou
    preencher(resp.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}
</script>
