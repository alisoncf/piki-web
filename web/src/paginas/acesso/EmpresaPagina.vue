<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'empresas' }" />
      <q-avatar v-if="!novo" text-color="white" size="30px" font-size="13px" class="q-mr-sm" :style="{ background: form.tema.principal }">
        {{ codigo }}
      </q-avatar>
      <div class="piki-titulo col">{{ novo ? 'Nova empresa' : form.nome || 'Empresa' }}</div>
      <q-badge v-if="!novo && !form.ativa" color="grey-6">Desativada</q-badge>
    </div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>

    <q-form v-else class="formulario" @submit.prevent="salvar">
      <section class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Identificação</div>
        <div class="row q-col-gutter-md">
          <q-input
            v-if="novo"
            v-model="codigo"
            outlined
            label="Código *"
            mask="##"
            hint="O mesmo do VB6 (01, 02...); não muda depois"
            :rules="[(v) => /^\d{2}$/.test(v || '') || 'Dois dígitos']"
            class="col-6 col-sm-3 col-md-2"
          />
          <q-input
            v-model="form.nome"
            outlined
            label="Nome curto *"
            hint="Aparece na escolha e na troca de empresa"
            maxlength="60"
            :rules="[(v) => !!v?.trim() || 'Informe o nome']"
            class="col-12 col-sm-6 col-md-4"
          />
          <q-input v-model="form.razao_social" outlined label="Razão social" maxlength="100" class="col-12 col-md-6" />
          <q-input v-model="form.nome_fantasia" outlined label="Nome fantasia" maxlength="60" class="col-12 col-md-6" />
          <q-input v-model="form.cnpj" outlined label="CNPJ" mask="##.###.###/####-##" unmasked-value class="col-12 col-sm-6 col-md-3" />
          <q-toggle v-model="form.ativa" label="Ativa" class="col-12 col-sm-6 col-md-3" />
        </div>
      </section>

      <section class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Fiscal</div>
        <div class="row q-col-gutter-md">
          <q-input v-model="form.inscricao_estadual" outlined label="Inscrição estadual" maxlength="20" class="col-12 col-sm-6 col-md-3" />
          <q-input v-model="form.inscricao_municipal" outlined label="Inscrição municipal" maxlength="20" class="col-12 col-sm-6 col-md-3" />
          <q-input v-model="form.suframa" outlined label="SUFRAMA" maxlength="19" class="col-12 col-sm-6 col-md-3" />
          <q-select v-model="form.crt" outlined label="Regime tributário (CRT)" :options="CRT" emit-value map-options clearable class="col-12 col-sm-6 col-md-3" />
          <q-select v-model="form.sped_perfil" outlined label="Perfil do SPED" :options="PERFIS_SPED" emit-value map-options clearable class="col-12 col-sm-6 col-md-3" />
          <q-select v-model="form.sped_atividade" outlined label="Atividade no SPED" :options="ATIVIDADES_SPED" emit-value map-options clearable class="col-12 col-sm-6 col-md-3" />
        </div>
      </section>

      <section class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Endereço e contato</div>
        <div class="row q-col-gutter-md">
          <campo-cep v-model="form.cep" label="CEP" :buscando="buscandoCep" class="col-12 col-sm-4 col-md-2" @buscar="buscarCep" />
          <q-input v-model="form.logradouro" outlined label="Logradouro" maxlength="60" class="col-12 col-sm-8 col-md-6" />
          <q-input v-model="form.numero" outlined label="Número" maxlength="10" class="col-6 col-sm-4 col-md-2" />
          <q-input v-model="form.complemento" outlined label="Complemento" maxlength="60" class="col-6 col-sm-8 col-md-2" />
          <q-input v-model="form.bairro" outlined label="Bairro" maxlength="60" class="col-12 col-sm-6 col-md-4" />
          <selecao-cidade v-model="form.cidade_id" v-model:cidade="cidade" class="col-12 col-sm-6 col-md-4" />
          <q-input
            v-model="form.telefone"
            outlined
            label="Telefone"
            :mask="mascaraTelefone(form.telefone)"
            unmasked-value
            class="col-12 col-sm-6 col-md-4"
          />
          <q-input v-model="form.email" outlined label="E-mail" type="email" maxlength="200" class="col-12 col-sm-6 col-md-6" />
        </div>
      </section>

      <section class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Cores na tela</div>
        <div class="text-caption text-suave q-mb-md">
          Para cada um saber em que loja está. Mudam quando o usuário entra ou troca de empresa; botões e links ficam na cor da marca.
        </div>
        <div class="row q-col-gutter-md items-start">
          <div class="col-12 col-md-6 row q-col-gutter-md">
            <campo-cor v-model="form.tema.principal" label="Principal" hint="Faixa do cabeçalho e selo da empresa" class="col-12" />
            <campo-cor v-model="form.tema.fundo" label="Fundo" hint="Fundo das telas" class="col-12 col-sm-6" />
            <campo-cor v-model="form.tema.menu" label="Menu" hint="Fundo do menu lateral" class="col-12 col-sm-6" />
            <div class="col-12">
              <q-btn flat no-caps color="primary" icon="auto_fix_high" label="Gerar fundo e menu a partir da principal" :disable="!corValida(form.tema.principal)" @click="gerarTema" />
            </div>
          </div>
          <div class="col-12 col-md-6">
            <!-- miniatura do sistema com as cores escolhidas -->
            <div class="previa" :style="{ background: form.tema.fundo }" aria-label="Prévia das cores">
              <div class="previa__menu" :style="{ background: form.tema.menu }">
                <div v-for="i in 4" :key="i" class="previa__item" />
              </div>
              <div class="previa__corpo">
                <div class="previa__cabecalho" :style="{ borderTopColor: form.tema.principal }">
                  <span class="previa__selo" :style="{ background: form.tema.principal }">{{ codigo || '00' }}</span>
                  {{ form.nome || 'Empresa' }}
                </div>
                <div class="previa__cartao">
                  <div class="previa__linha" />
                  <div class="previa__linha previa__linha--curta" />
                  <q-btn unelevated dense no-caps color="primary" label="Salvar" size="sm" tabindex="-1" class="q-mt-sm" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section v-if="!novo" class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Imagens</div>
        <div class="row q-col-gutter-lg">
          <div v-for="img in IMAGENS" :key="img.tipo" class="col-12 col-sm-6">
            <div class="text-weight-medium">{{ img.titulo }}</div>
            <div class="text-caption text-suave q-mb-sm">{{ img.uso }} PNG ou JPEG, até 1 MB.</div>
            <div class="imagem row items-center justify-center q-mb-sm">
              <img v-if="imagens[img.tipo]" :src="imagens[img.tipo]" :alt="img.titulo" />
              <span v-else class="text-suave">Sem imagem</span>
            </div>
            <input :ref="(el) => (seletores[img.tipo] = el)" type="file" accept="image/png,image/jpeg" hidden @change="(ev) => enviar(img.tipo, ev)" />
            <q-btn flat no-caps color="primary" icon="upload" :label="imagens[img.tipo] ? 'Trocar' : 'Enviar'" :loading="enviando === img.tipo" @click="seletores[img.tipo].click()" />
            <q-btn v-if="imagens[img.tipo]" flat no-caps color="negative" icon="delete" label="Remover" @click="remover(img.tipo)" />
          </div>
        </div>
      </section>

      <section v-if="!novo && notas" class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Notas fiscais (NFC-e e NF-e)</div>
        <div class="row q-col-gutter-md items-start">
          <div class="col-12 col-md-6">
            <div class="text-weight-medium q-mb-xs">Ambiente da SEFAZ</div>
            <q-btn-toggle
              v-model="notas.ambiente"
              no-caps
              unelevated
              toggle-color="primary"
              :options="[{ label: 'Homologação (testes)', value: '2' }, { label: 'Produção', value: '1' }]"
            />
            <div class="text-weight-medium q-mt-md q-mb-xs">CSC da NFC-e</div>
            <div class="row q-col-gutter-sm">
              <q-input v-model="notas.csc_id" outlined dense label="Id do CSC" maxlength="10" class="col-4" />
              <q-input
                v-model="notas.csc_token"
                outlined
                dense
                type="password"
                autocomplete="new-password"
                label="Token do CSC"
                :hint="notas.tem_csc ? 'Já cadastrado; preencha só para trocar' : 'Guardado cifrado; não aparece de novo'"
                maxlength="50"
                class="col-8"
              />
            </div>
            <q-btn flat no-caps color="primary" icon="check" label="Salvar ambiente e CSC" class="q-mt-sm" :loading="salvandoNotas" @click="salvarNotas" />
          </div>
          <div class="col-12 col-md-6">
            <div class="text-weight-medium q-mb-xs">Certificado digital A1</div>
            <div v-if="notas.certificado" class="q-mb-sm">
              <div class="text-caption">{{ notas.certificado.titular }}</div>
              <q-badge :color="notas.certificado.dias_para_vencer < 30 ? 'negative' : 'positive'">
                Vence em {{ formatarDataHora(notas.certificado.validade).slice(0, 10) }} ({{ notas.certificado.dias_para_vencer }} dias)
              </q-badge>
            </div>
            <div v-else class="text-caption text-suave q-mb-sm">Nenhum certificado enviado.</div>
            <input ref="seletorCertificado" type="file" accept=".pfx,.p12" hidden @change="escolherCertificado" />
            <div class="row q-col-gutter-sm items-center">
              <div class="col-12">
                <q-btn flat no-caps icon="attach_file" :label="certificado.nome || 'Escolher o arquivo .pfx'" @click="seletorCertificado.click()" />
              </div>
              <q-input v-model="certificado.senha" outlined dense type="password" autocomplete="new-password" label="Senha do certificado" class="col" />
              <div class="col-auto">
                <q-btn unelevated no-caps color="primary" icon="upload" label="Enviar" :disable="!certificado.arquivo || !certificado.senha" :loading="enviandoCertificado" @click="enviarCertificado" />
              </div>
            </div>
            <div class="text-caption text-suave q-mt-xs">O arquivo fica numa pasta do servidor; a senha, cifrada no banco.</div>
          </div>
        </div>
      </section>

      <div class="formulario__acoes row justify-end q-gutter-sm q-mb-md">
        <q-btn flat no-caps label="Cancelar" :to="{ name: 'empresas' }" />
        <q-btn type="submit" color="primary" unelevated no-caps icon="check" label="Salvar" :loading="salvando" />
      </div>
    </q-form>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import CampoCep from '@/componentes/CampoCep.vue'
import CampoCor from '@/componentes/CampoCor.vue'
import SelecaoCidade from '@/componentes/SelecaoCidade.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { usarCep } from '@/servicos/cep'
import { formatarDataHora, mascaraTelefone } from '@/servicos/formatos'
import { temaDaCor } from '@/servicos/tema'
import { useSessaoStore } from '@/stores/sessao'

// mesmos códigos da NF-e e do SPED Fiscal
const CRT = [
  { value: '1', label: '1 - Simples Nacional' },
  { value: '2', label: '2 - Simples Nacional, excesso de sublimite' },
  { value: '3', label: '3 - Regime normal' },
]
const PERFIS_SPED = ['A', 'B', 'C'].map((p) => ({ value: p, label: `Perfil ${p}` }))
const ATIVIDADES_SPED = [
  { value: '0', label: '0 - Industrial ou equiparado' },
  { value: '1', label: '1 - Outros' },
]
const IMAGENS = [
  { tipo: 'logo', titulo: 'Logo', uso: 'Sai nos relatórios.' },
  { tipo: 'qrcode', titulo: 'QR code', uso: 'Sai no boleto de cobrança.' },
]

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()

const novo = computed(() => !rota.params.id)
const carregando = ref(true)
const salvando = ref(false)
const codigo = ref('')
const cidade = ref(null) // { id, nome, uf }, para o campo mostrar o nome
const imagens = ref({}) // tipo → endereço local da imagem baixada
const seletores = {}
const enviando = ref(null)

function vazio() {
  return {
    nome: '', razao_social: '', nome_fantasia: '', cnpj: '', inscricao_estadual: '', inscricao_municipal: '', suframa: '',
    crt: null, sped_perfil: null, sped_atividade: null,
    cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade_id: null, telefone: '', email: '',
    ativa: true, tema: temaDaCor('#2f6fb0'),
  }
}
const form = ref(vazio())

const { buscando: buscandoCep, buscar: buscarCep } = usarCep(
  form, { cep: 'cep', rua: 'logradouro', bairro: 'bairro', cidade: 'cidade_id' }, { cidade },
)

function corValida(cor) {
  return /^#[0-9a-f]{6}$/.test(cor || '')
}

function gerarTema() {
  form.value.tema = temaDaCor(form.value.tema.principal)
}

function preencher(empresa) {
  const { id, codigo: cod, cidade: cid, imagens: tipos, criado_em, atualizado_em, ...dados } = empresa
  codigo.value = cod
  cidade.value = cid
  form.value = { ...vazio(), ...dados, tema: { ...dados.tema } }
  return tipos
}

function soltarImagens() {
  Object.values(imagens.value).forEach((url) => URL.revokeObjectURL(url))
  imagens.value = {}
}

// as imagens pedem login, então vêm pela API e não direto no <img>
async function carregarImagens(tipos) {
  soltarImagens()
  for (const tipo of tipos) {
    const { data } = await api.get(`/empresas/${rota.params.id}/imagens/${tipo}`, { responseType: 'blob' })
    imagens.value = { ...imagens.value, [tipo]: URL.createObjectURL(data) }
  }
}

// notas fiscais: ambiente, CSC e certificado (D29); a senha e o token nunca voltam da API
const notas = ref(null)
const salvandoNotas = ref(false)
const seletorCertificado = ref(null)
const certificado = ref({ nome: '', arquivo: '', senha: '' })
const enviandoCertificado = ref(false)

function mostrarNotas(dados) {
  notas.value = { ...dados, csc_id: dados.csc_id ?? '', csc_token: '' }
}

async function salvarNotas() {
  salvandoNotas.value = true
  try {
    const { ambiente, csc_id, csc_token } = notas.value
    mostrarNotas((await api.put(`/empresas/${rota.params.id}/fiscal`, { ambiente, csc_id: csc_id || null, csc_token: csc_token || null })).data)
    $q.notify({ type: 'positive', message: 'Dados das notas salvos' })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvandoNotas.value = false
  }
}

function escolherCertificado(evento) {
  const arquivo = evento.target.files?.[0]
  evento.target.value = ''
  if (!arquivo) return
  const leitor = new FileReader()
  leitor.onload = () => (certificado.value = { ...certificado.value, nome: arquivo.name, arquivo: String(leitor.result).split(',')[1] })
  leitor.readAsDataURL(arquivo)
}

async function enviarCertificado() {
  enviandoCertificado.value = true
  try {
    const { arquivo, senha } = certificado.value
    mostrarNotas((await api.put(`/empresas/${rota.params.id}/certificado`, { arquivo, senha })).data)
    certificado.value = { nome: '', arquivo: '', senha: '' }
    $q.notify({ type: 'positive', message: 'Certificado enviado' })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    enviandoCertificado.value = false
  }
}

onMounted(async () => {
  try {
    if (!novo.value) {
      await carregarImagens(preencher((await api.get(`/empresas/${rota.params.id}`)).data))
      mostrarNotas((await api.get(`/empresas/${rota.params.id}/fiscal`)).data)
    }
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

onBeforeUnmount(soltarImagens)

async function salvar() {
  salvando.value = true
  try {
    const resp = novo.value
      ? await api.post('/empresas', { ...form.value, codigo: codigo.value })
      : await api.put(`/empresas/${rota.params.id}`, form.value)
    $q.notify({ type: 'positive', message: 'Empresa salva', timeout: 1500 })
    // as cores e o nome da empresa em que o usuário está mudam na hora
    if (sessao.empresas.some((e) => e.id === resp.data.id)) await sessao.carregarEu()
    if (novo.value) await roteador.replace({ name: 'empresa', params: { id: resp.data.id } })
    preencher(resp.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

async function enviar(tipo, evento) {
  const arquivo = evento.target.files?.[0]
  evento.target.value = '' // permite escolher o mesmo arquivo de novo
  if (!arquivo) return
  enviando.value = tipo
  try {
    const { data } = await api.put(`/empresas/${rota.params.id}/imagens/${tipo}`, arquivo, {
      headers: { 'Content-Type': arquivo.type || 'application/octet-stream' },
    })
    await carregarImagens(data.imagens)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    enviando.value = null
  }
}

function remover(tipo) {
  $q.dialog({
    title: 'Remover imagem',
    message: `Remover o ${IMAGENS.find((i) => i.tipo === tipo).titulo.toLowerCase()} da empresa?`,
    cancel: { flat: true, label: 'Não' },
    ok: { label: 'Remover', color: 'negative' },
  }).onOk(async () => {
    try {
      const { data } = await api.delete(`/empresas/${rota.params.id}/imagens/${tipo}`)
      await carregarImagens(data.imagens)
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}
</script>

<style scoped>
.previa {
  display: flex;
  height: 170px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--piki-borda);
}
.previa__menu {
  width: 70px;
  padding: 14px 10px;
}
.previa__item {
  height: 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.25);
  margin-bottom: 10px;
}
.previa__corpo {
  flex: 1;
  min-width: 0;
}
.previa__cabecalho {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 12px;
  background: #fff;
  border-top: 4px solid;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
}
.previa__selo {
  color: #fff;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  font-size: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.previa__cartao {
  margin: 14px;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
}
.previa__linha {
  height: 8px;
  border-radius: 4px;
  background: #e6e6e6;
  margin-bottom: 8px;
}
.previa__linha--curta {
  width: 60%;
}
.imagem {
  height: 120px;
  border: 1px dashed var(--piki-borda);
  border-radius: 8px;
  background: #fff;
}
.imagem img {
  max-height: 110px;
  max-width: 100%;
  object-fit: contain;
}
</style>
