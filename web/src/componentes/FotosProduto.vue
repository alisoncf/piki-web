<template>
  <!-- fotos do produto: a primeira é a principal (aparece nas listas e no PDV) -->
  <div>
    <div v-if="podeEditar" class="row q-gutter-sm q-mb-md">
      <q-btn flat no-caps color="primary" icon="photo_camera" label="Tirar foto" :loading="enviando" @click="camera.click()" />
      <q-btn flat no-caps color="primary" icon="add_photo_alternate" label="Enviar foto" :loading="enviando" @click="seletor.click()" />
      <input ref="camera" type="file" accept="image/*" capture="environment" hidden @change="escolher" />
      <input ref="seletor" type="file" accept="image/jpeg,image/png" multiple hidden @change="escolher" />
    </div>
    <div v-if="!fotos.length" class="text-suave">Nenhuma foto.</div>
    <div v-else class="row q-col-gutter-md">
      <div v-for="(foto, i) in fotos" :key="foto.id" class="col-6 col-sm-4 col-md-3 col-lg-2">
        <div class="foto">
          <div class="foto__imagem row items-center justify-center">
            <img v-if="imagens[foto.id]" :src="imagens[foto.id]" :alt="`Foto ${i + 1}`" />
            <q-spinner v-else color="grey-6" />
            <q-badge v-if="i === 0" color="primary" class="foto__principal">Principal</q-badge>
          </div>
          <div v-if="podeEditar" class="row justify-end q-pa-xs">
            <q-btn v-if="i > 0" flat round dense icon="star_outline" aria-label="Tornar principal" @click="principal(foto)">
              <q-tooltip>Tornar principal</q-tooltip>
            </q-btn>
            <q-btn flat round dense icon="delete_outline" color="grey-7" aria-label="Remover foto" @click="remover(foto)" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { onBeforeUnmount, ref, watch } from 'vue'

import { api, mensagemDeErro } from '@/servicos/api'
import { reduzirImagem } from '@/servicos/imagens'

const props = defineProps({
  produtoId: { type: Number, required: true },
  modelValue: { type: Array, required: true }, // [{ id, ordem, tamanho }]
  podeEditar: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const $q = useQuasar()
const base = `/produtos/${props.produtoId}/fotos`
const fotos = ref([...props.modelValue])
const imagens = ref({}) // id → endereço local da imagem baixada
const camera = ref(null)
const seletor = ref(null)
const enviando = ref(false)

// as fotos pedem login, então vêm pela API como blob e não direto no <img>
async function baixar(foto) {
  if (imagens.value[foto.id]) return
  try {
    const { data } = await api.get(`${base}/${foto.id}/arquivo`, { responseType: 'blob' })
    imagens.value = { ...imagens.value, [foto.id]: URL.createObjectURL(data) }
  } catch {
    /* fica o indicador */
  }
}

watch(() => props.modelValue, (v) => {
  fotos.value = [...v]
  fotos.value.forEach(baixar)
}, { immediate: true })

onBeforeUnmount(() => Object.values(imagens.value).forEach((url) => URL.revokeObjectURL(url)))

function atualizar(lista) {
  fotos.value = lista
  emit('update:modelValue', lista)
}

async function escolher(evento) {
  const arquivos = [...(evento.target.files ?? [])]
  evento.target.value = '' // permite escolher o mesmo arquivo de novo
  if (!arquivos.length) return
  enviando.value = true
  try {
    for (const original of arquivos) {
      const arquivo = await reduzirImagem(original, { lado: 1200 })
      const { data } = await api.post(base, arquivo, { headers: { 'Content-Type': arquivo.type || 'image/jpeg' } })
      atualizar([...fotos.value, data])
      baixar(data)
    }
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    enviando.value = false
  }
}

async function principal(foto) {
  try {
    atualizar((await api.post(`${base}/${foto.id}/principal`)).data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

function remover(foto) {
  $q.dialog({
    title: 'Remover foto',
    message: 'Remover esta foto do produto?',
    cancel: { flat: true, label: 'Não' },
    ok: { label: 'Remover', color: 'negative' },
  }).onOk(async () => {
    try {
      await api.delete(`${base}/${foto.id}`)
      atualizar(fotos.value.filter((f) => f.id !== foto.id))
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}
</script>

<style scoped>
.foto {
  border: 1px solid var(--piki-borda);
  border-radius: 8px;
  background: var(--piki-superficie);
  overflow: hidden;
}
.foto__imagem {
  position: relative;
  height: 140px;
  background: #f4f4f4;
}
.foto__imagem img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.foto__principal {
  position: absolute;
  top: 6px;
  left: 6px;
}
</style>
