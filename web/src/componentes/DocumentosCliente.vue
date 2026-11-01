<template>
  <!-- documentos do crediário: só aparece para quem tem clientes.documentos (LGPD) -->
  <section class="cartao q-pa-md q-mb-md">
    <div class="row items-center q-mb-md">
      <div class="formulario__secao col q-mb-none">Documentos</div>
      <q-btn flat no-caps color="primary" icon="photo_camera" label="Tirar foto" @click="camera.click()" />
      <q-btn flat no-caps color="primary" icon="upload_file" label="Enviar arquivo" @click="seletor.click()" />
      <input ref="camera" type="file" accept="image/*" capture="environment" hidden @change="escolher" />
      <input ref="seletor" type="file" accept="application/pdf,image/jpeg,image/png" hidden @change="escolher" />
    </div>

    <div v-if="carregando" class="row justify-center q-pa-md"><q-spinner color="primary" size="30px" /></div>
    <div v-else-if="!documentos.length" class="text-suave">Nenhum documento.</div>
    <div v-else class="row q-col-gutter-md">
      <div v-for="doc in documentos" :key="doc.id" class="col-6 col-sm-4 col-md-3 col-lg-2">
        <div class="documento" role="button" tabindex="0" :aria-label="`Abrir ${nomeTipoDocumento(doc.tipo)}`" @click="abrir(doc)" @keydown.enter="abrir(doc)">
          <div class="documento__miniatura row items-center justify-center">
            <img v-if="miniaturas[doc.id]" :src="miniaturas[doc.id]" :alt="doc.nome_arquivo" />
            <q-icon v-else :name="doc.tipo_conteudo === 'application/pdf' ? 'picture_as_pdf' : 'image'" size="40px" color="grey-6" />
          </div>
          <div class="q-pa-sm">
            <div class="text-weight-medium ellipsis">{{ nomeTipoDocumento(doc.tipo) }}</div>
            <div v-if="doc.descricao" class="text-caption ellipsis">{{ doc.descricao }}</div>
            <div class="text-caption text-suave ellipsis">
              {{ formatarDataHora(doc.data_hora) }}<template v-if="doc.usuario"> · {{ doc.usuario.nome }}</template><template v-if="doc.empresa"> · {{ doc.empresa.nome }}</template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- tipo e descrição do arquivo escolhido -->
    <q-dialog v-model="pedindo" persistent>
      <q-card style="width: 420px; max-width: 92vw">
        <q-form @submit.prevent="enviar">
          <q-card-section class="text-h6">Novo documento</q-card-section>
          <q-card-section class="q-gutter-md">
            <div class="text-caption text-suave ellipsis">{{ novo.arquivo?.name }}</div>
            <q-select
              v-model="novo.tipo"
              outlined
              label="Tipo *"
              :options="TIPOS_DOCUMENTO"
              emit-value
              map-options
              :rules="[(v) => !!v || 'Escolha o tipo']"
            />
            <q-input v-model="novo.descricao" outlined label="Descrição" hint="Frente, verso, conta de luz..." maxlength="60" />
          </q-card-section>
          <q-card-actions align="right">
            <q-btn v-close-popup flat no-caps label="Cancelar" :disable="enviando" />
            <q-btn type="submit" color="primary" unelevated no-caps icon="upload" label="Enviar" :loading="enviando" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- documento aberto -->
    <q-dialog v-model="vendo" maximized @hide="fecharVisualizacao">
      <q-card v-if="aberto" class="column no-wrap">
        <q-card-section class="row items-center q-py-sm">
          <div class="col">
            <div class="text-weight-medium">{{ nomeTipoDocumento(aberto.doc.tipo) }}<template v-if="aberto.doc.descricao"> · {{ aberto.doc.descricao }}</template></div>
            <div class="text-caption text-suave">{{ aberto.doc.nome_arquivo }} · {{ formatarTamanho(aberto.doc.tamanho) }}</div>
          </div>
          <q-btn v-if="aberto.url" flat no-caps color="primary" icon="download" label="Baixar" :href="aberto.url" :download="aberto.doc.nome_arquivo" />
          <q-btn v-if="podeRemover" flat no-caps color="negative" icon="delete" label="Remover" @click="remover(aberto.doc)" />
          <q-btn v-close-popup flat round dense icon="close" aria-label="Fechar" />
        </q-card-section>
        <q-separator />
        <div class="col documento__visualizacao row items-center justify-center">
          <q-spinner v-if="!aberto.url" color="primary" size="40px" />
          <iframe v-else-if="aberto.doc.tipo_conteudo === 'application/pdf'" :src="aberto.url" :title="aberto.doc.nome_arquivo" />
          <img v-else :src="aberto.url" :alt="aberto.doc.nome_arquivo" />
        </div>
      </q-card>
    </q-dialog>
  </section>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onBeforeUnmount, onMounted, ref } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora, formatarTamanho, nomeTipoDocumento, TIPOS_DOCUMENTO } from '@/servicos/formatos'
import { reduzirImagem } from '@/servicos/imagens'

const props = defineProps({
  clienteId: { type: Number, required: true },
  // remover pede também clientes.editar
  podeRemover: { type: Boolean, default: false },
})

const $q = useQuasar()
const base = `/clientes/${props.clienteId}/documentos`

const documentos = ref([])
const carregando = ref(true)
const miniaturas = ref({}) // id → endereço local da imagem baixada
const camera = ref(null)
const seletor = ref(null)
const pedindo = ref(false)
const novo = ref({ arquivo: null, tipo: null, descricao: '' })
const enviando = ref(false)
const vendo = ref(false)
const aberto = ref(null) // { doc, url }

// os arquivos pedem login, então vêm pela API como blob e não direto no <img>
async function baixar(doc) {
  const { data } = await api.get(`${base}/${doc.id}/arquivo`, { responseType: 'blob' })
  return URL.createObjectURL(data)
}

async function carregarMiniatura(doc) {
  if (!doc.tipo_conteudo.startsWith('image/')) return
  try {
    miniaturas.value = { ...miniaturas.value, [doc.id]: await baixar(doc) }
  } catch {
    /* sem miniatura, fica o ícone */
  }
}

onMounted(async () => {
  try {
    documentos.value = (await api.get(base)).data
    documentos.value.forEach(carregarMiniatura)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

onBeforeUnmount(() => {
  Object.values(miniaturas.value).forEach((url) => URL.revokeObjectURL(url))
  fecharVisualizacao()
})

function escolher(evento) {
  const arquivo = evento.target.files?.[0]
  evento.target.value = '' // permite escolher o mesmo arquivo de novo
  if (!arquivo) return
  novo.value = { arquivo, tipo: null, descricao: '' }
  pedindo.value = true
}

async function enviar() {
  enviando.value = true
  try {
    const arquivo = await reduzirImagem(novo.value.arquivo)
    const { data } = await api.post(base, arquivo, {
      params: { tipo: novo.value.tipo, descricao: novo.value.descricao || undefined, nome: arquivo.name },
      headers: { 'Content-Type': arquivo.type || 'application/octet-stream' },
    })
    documentos.value = [data, ...documentos.value]
    carregarMiniatura(data)
    pedindo.value = false
    $q.notify({ type: 'positive', message: 'Documento enviado', timeout: 1500 })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    enviando.value = false
  }
}

async function abrir(doc) {
  aberto.value = { doc, url: null }
  vendo.value = true
  try {
    const url = await baixar(doc)
    if (aberto.value?.doc.id === doc.id) aberto.value = { doc, url }
    else URL.revokeObjectURL(url)
  } catch (e) {
    vendo.value = false
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

function fecharVisualizacao() {
  if (aberto.value?.url) URL.revokeObjectURL(aberto.value.url)
  aberto.value = null
}

function remover(doc) {
  $q.dialog({
    title: 'Remover documento',
    message: `Remover ${nomeTipoDocumento(doc.tipo).toLowerCase()} da lista? O arquivo continua guardado, com o registro de quem removeu.`,
    cancel: { flat: true, label: 'Não' },
    ok: { label: 'Remover', color: 'negative' },
  }).onOk(async () => {
    try {
      await api.delete(`${base}/${doc.id}`)
      documentos.value = documentos.value.filter((d) => d.id !== doc.id)
      vendo.value = false
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}
</script>

<style scoped>
.documento {
  border: 1px solid var(--piki-borda);
  border-radius: 8px;
  background: var(--piki-superficie);
  cursor: pointer;
  overflow: hidden;
}
.documento:hover,
.documento:focus-visible {
  border-color: var(--q-primary);
}
.documento__miniatura {
  height: 110px;
  background: #f4f4f4;
}
.documento__miniatura img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.documento__visualizacao {
  min-height: 0;
  background: #2a2a2a;
}
.documento__visualizacao img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.documento__visualizacao iframe {
  width: 100%;
  height: 100%;
  border: 0;
  background: #fff;
}
</style>
