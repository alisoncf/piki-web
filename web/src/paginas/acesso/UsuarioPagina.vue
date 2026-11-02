<template>
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'usuarios' }" />
      <div class="piki-titulo col">{{ novo ? 'Novo usuário' : form.nome || 'Usuário' }}</div>
      <q-badge v-if="!novo && !form.ativo" color="grey-6" class="q-mr-xs">Inativo</q-badge>
      <q-badge v-if="bloqueado" color="negative" class="q-mr-xs">Bloqueado</q-badge>
      <q-badge v-else-if="info?.trocar_senha" color="warning" text-color="dark">Senha provisória</q-badge>
    </div>
    <div v-if="info?.ultimo_login" class="text-caption text-suave q-mb-md">Último acesso em {{ formatarDataHora(info.ultimo_login) }}</div>

    <div v-if="carregando" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>

    <template v-else>
      <q-form class="formulario" @submit.prevent="salvar">
        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Identificação</div>
          <div class="row q-col-gutter-md">
            <selecao-busca
              v-if="podeVerFuncionarios"
              v-model="form.funcionario_id"
              :opcoes="funcionarios"
              :rotulo="nomeFuncionario"
              label="Funcionário"
              hint="Quem usa este login; deixe vazio para quem não é funcionário (contador, suporte)"
              class="col-12 col-md-6"
              @update:model-value="sugerirDoFuncionario"
            />
            <q-input
              v-else
              :model-value="info?.funcionario ? nomeFuncionario(info.funcionario) : 'Nenhum'"
              outlined
              readonly
              label="Funcionário"
              class="col-12 col-md-6"
            />
            <q-input
              v-model="form.nome"
              outlined
              label="Nome *"
              maxlength="80"
              :rules="[(v) => !!v?.trim() || 'Informe o nome']"
              class="col-12 col-md-6"
            />
            <q-input
              v-model="form.login"
              outlined
              label="Usuário (login) *"
              maxlength="30"
              :rules="[(v) => /^\S+$/.test(v || '') || 'Sem espaços']"
              class="col-12 col-sm-6 col-md-3"
            />
            <q-input
              v-model="form.email"
              outlined
              type="email"
              label="E-mail"
              hint="Para recuperar a senha"
              maxlength="200"
              class="col-12 col-sm-6 col-md-5"
            />
            <div class="col-12 col-md-4 row items-center q-gutter-x-md">
              <q-toggle v-model="form.ativo" label="Ativo" />
              <q-toggle v-if="sessao.usuario?.administrador" v-model="form.administrador" label="Administrador" />
            </div>
          </div>
        </section>

        <section v-if="novo" class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Senha provisória</div>
          <div class="text-caption text-suave q-mb-md">Passe esta senha para a pessoa; no primeiro login ela cria a senha dela.</div>
          <div class="row q-col-gutter-md">
            <q-input
              v-model="senha"
              outlined
              label="Senha provisória *"
              maxlength="100"
              :rules="[(v) => (v || '').length >= 8 || 'Pelo menos 8 caracteres']"
              class="col-12 col-sm-6 col-md-4"
            >
              <template #append>
                <q-btn flat round dense icon="casino" aria-label="Gerar uma senha" @click="senha = gerarSenha()">
                  <q-tooltip>Gerar uma senha</q-tooltip>
                </q-btn>
              </template>
            </q-input>
            <q-select
              v-if="!sessao.usuario?.administrador"
              v-model="perfilNovo"
              outlined
              :label="`Perfil em ${sessao.empresa?.nome} *`"
              :options="perfis"
              option-value="id"
              option-label="nome"
              emit-value
              map-options
              :rules="[(v) => !!v || 'Escolha o perfil']"
              class="col-12 col-sm-6 col-md-4"
            />
          </div>
        </section>

        <div class="formulario__acoes row justify-end q-gutter-sm q-mb-md">
          <q-btn flat no-caps label="Cancelar" :to="{ name: 'usuarios' }" />
          <q-btn type="submit" color="primary" unelevated no-caps icon="check" label="Salvar" :loading="salvando" />
        </div>
      </q-form>

      <template v-if="!novo">
        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Senha e bloqueio</div>
          <div class="row items-center q-gutter-sm">
            <q-btn outline no-caps color="primary" icon="key" label="Definir senha provisória" @click="pedirSenha" />
            <q-btn v-if="bloqueado" outline no-caps color="negative" icon="lock_open" label="Desbloquear" @click="desbloquear" />
            <span v-if="bloqueado" class="text-caption text-suave">
              Bloqueado até {{ formatarDataHora(info.bloqueado_ate) }} por excesso de senhas erradas.
            </span>
          </div>
        </section>

        <section class="cartao q-pa-md q-mb-md">
          <div class="formulario__secao">Empresas e perfis</div>
          <div v-if="form.administrador" class="text-suave">Administrador: entra em todas as empresas, com todas as permissões.</div>
          <template v-else>
            <div class="text-caption text-suave q-mb-md">Em cada empresa, o perfil diz o que a pessoa pode fazer nela.</div>
            <div v-for="emp in empresasDaTela" :key="emp.id" class="row items-center q-col-gutter-md q-mb-sm acesso">
              <div class="col-12 col-sm-4 row items-center no-wrap">
                <q-avatar text-color="white" size="26px" font-size="12px" class="q-mr-sm" :style="{ background: emp.tema.principal }">
                  {{ emp.codigo }}
                </q-avatar>
                {{ emp.nome }}
              </div>
              <q-select
                :model-value="acessos[emp.id]?.perfil_id ?? null"
                outlined
                dense
                label="Perfil"
                :options="perfis"
                option-value="id"
                option-label="nome"
                emit-value
                map-options
                :disable="!podeMexerEm(emp)"
                class="col-8 col-sm-4"
                @update:model-value="(perfilId) => salvarAcesso(emp, perfilId, true)"
              />
              <div class="col-4 col-sm-4">
                <q-toggle
                  :model-value="!!acessos[emp.id]?.ativo"
                  label="Acesso"
                  :disable="!podeMexerEm(emp) || !acessos[emp.id]"
                  @update:model-value="(ativo) => salvarAcesso(emp, acessos[emp.id].perfil_id, ativo)"
                />
              </div>
            </div>
          </template>
        </section>
      </template>
    </template>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SelecaoBusca from '@/componentes/SelecaoBusca.vue'
import { api, mensagemDeErro } from '@/servicos/api'
import { formatarDataHora } from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()

const novo = computed(() => !rota.params.id)
const podeVerFuncionarios = computed(() => sessao.pode('funcionarios.ver'))
const carregando = ref(true)
const salvando = ref(false)
const info = ref(null) // o que vem da API e não se edita aqui: acessos, bloqueio, último acesso
const funcionarios = ref([])
const perfis = ref([])
const senha = ref('')
const perfilNovo = ref(null)

function vazio() {
  return { nome: '', login: '', email: '', funcionario_id: null, ativo: true, administrador: false }
}
const form = ref(vazio())

const bloqueado = computed(() => !!info.value?.bloqueado_ate && new Date(info.value.bloqueado_ate) > new Date())
// empresa id → { perfil_id, ativo }
const acessos = computed(() => Object.fromEntries((info.value?.acessos ?? []).map((a) => [a.empresa.id, { perfil_id: a.perfil.id, ativo: a.ativo }])))
// as empresas em que quem está na tela entra (o administrador, todas), mais as que o usuário já tem
const empresasDaTela = computed(() => {
  const lista = [...sessao.empresas]
  for (const a of info.value?.acessos ?? []) if (!lista.some((e) => e.id === a.empresa.id)) lista.push(a.empresa)
  return lista.sort((a, b) => a.codigo.localeCompare(b.codigo))
})

// quem não é administrador só mexe no acesso da empresa em que está (e não no próprio)
function podeMexerEm(emp) {
  if (sessao.usuario?.administrador) return true
  return emp.id === sessao.empresa?.id && info.value?.id !== sessao.usuario?.id
}

function nomeFuncionario(f) {
  return f ? (f.apelido ? `${f.nome} (${f.apelido})` : f.nome) : ''
}

// ao escolher o funcionário num usuário novo, o nome e o login vêm dele
function sugerirDoFuncionario(id) {
  const f = funcionarios.value.find((x) => x.id === id)
  if (!f || !novo.value) return
  if (!form.value.nome.trim()) form.value.nome = f.nome
  if (!form.value.login.trim()) form.value.login = (f.apelido || f.nome.split(' ')[0]).trim().toLowerCase().replace(/\s+/g, '.')
}

function gerarSenha() {
  // sem letras e números que se confundem (l, 1, O, 0)
  const letras = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  const sorteio = crypto.getRandomValues(new Uint32Array(10))
  return Array.from(sorteio, (n) => letras[n % letras.length]).join('')
}

function preencher(usuario) {
  info.value = usuario
  const { nome, login, email, ativo, administrador, funcionario } = usuario
  form.value = { nome, login, email: email ?? '', ativo, administrador, funcionario_id: funcionario?.id ?? null }
  if (funcionario && !funcionarios.value.some((f) => f.id === funcionario.id)) funcionarios.value = [...funcionarios.value, funcionario]
}

onMounted(async () => {
  try {
    const pedidos = [api.get('/acesso/perfis').then((r) => (perfis.value = r.data))]
    if (podeVerFuncionarios.value) pedidos.push(api.get('/funcionarios', { params: { so_ativos: true } }).then((r) => (funcionarios.value = r.data)))
    if (!novo.value) pedidos.push(api.get(`/acesso/usuarios/${rota.params.id}`).then((r) => preencher(r.data)))
    await Promise.all(pedidos)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    carregando.value = false
  }
})

async function salvar() {
  salvando.value = true
  try {
    const dados = { ...form.value, email: form.value.email || null }
    const resp = novo.value
      ? await api.post('/acesso/usuarios', { ...dados, senha: senha.value, perfil_id: perfilNovo.value })
      : await api.put(`/acesso/usuarios/${rota.params.id}`, dados)
    $q.notify({ type: 'positive', message: 'Usuário salvo', timeout: 1500 })
    if (novo.value) await roteador.replace({ name: 'usuario', params: { id: resp.data.id } })
    preencher(resp.data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = false
  }
}

async function salvarAcesso(emp, perfilId, ativo) {
  try {
    const { data } = await api.put(`/acesso/usuarios/${info.value.id}/acessos/${emp.id}`, { perfil_id: perfilId, ativo })
    preencher(data)
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

function pedirSenha() {
  $q.dialog({
    title: 'Senha provisória',
    message: 'Passe esta senha para a pessoa. No próximo login ela vai criar a senha dela. O login também é desbloqueado.',
    prompt: { model: gerarSenha(), type: 'text', isValid: (v) => (v || '').length >= 8 },
    cancel: { flat: true, label: 'Cancelar' },
    ok: { label: 'Definir' },
    persistent: true,
  }).onOk(async (nova) => {
    try {
      preencher((await api.put(`/acesso/usuarios/${info.value.id}/senha`, { senha: nova })).data)
      $q.notify({ type: 'positive', message: 'Senha provisória definida', timeout: 1500 })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    }
  })
}

async function desbloquear() {
  try {
    preencher((await api.post(`/acesso/usuarios/${info.value.id}/desbloquear`)).data)
    $q.notify({ type: 'positive', message: 'Login desbloqueado', timeout: 1500 })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}
</script>
