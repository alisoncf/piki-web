<template>
  <!-- a ficha do representante (D30): os dados pessoais são os do cliente; aqui, os do consignado -->
  <q-page padding>
    <div class="row items-center q-mb-md">
      <q-btn flat round dense icon="arrow_back" aria-label="Voltar" class="q-mr-sm" :to="{ name: 'representantes' }" />
      <div class="piki-titulo col">{{ rep ? `Representante ${rep.codigo} · ${rep.cliente.nome}` : 'Representante' }}</div>
      <template v-if="rep">
        <q-badge v-if="!rep.ativo" color="grey">Inativo</q-badge>
        <q-badge v-else :color="rep.bloqueado ? 'negative' : 'positive'">{{ rep.bloqueado ? 'Bloqueado' : 'Liberado' }}</q-badge>
      </template>
    </div>

    <div v-if="!rep" class="row justify-center q-pa-xl"><q-spinner color="primary" size="40px" /></div>
    <template v-else>
      <q-banner v-if="rep.lembrete" rounded class="bg-amber-1 q-mb-md"><q-icon name="push_pin" class="q-mr-sm" />{{ rep.lembrete }}</q-banner>

      <section class="cartao q-pa-md q-mb-md">
        <div class="row items-center">
          <div class="formulario__secao col">Dados pessoais (ficha do cliente)</div>
          <q-btn flat no-caps color="primary" icon="open_in_new" label="Abrir a ficha do cliente" :to="{ name: 'cliente', params: { id: rep.cliente.id } }" />
        </div>
        <div class="row q-col-gutter-md">
          <div class="col-12 col-sm-4"><div class="text-caption text-suave">CPF</div>{{ rep.cliente.cpf_cnpj ? formatarDocumento(rep.cliente.cpf_cnpj) : '—' }}</div>
          <div class="col-12 col-sm-8"><div class="text-caption text-suave">Endereço</div>{{ endereco || '—' }}</div>
          <div class="col-12 col-sm-4"><div class="text-caption text-suave">Telefones</div>{{ rep.cliente.telefones.map((t) => formatarTelefone(t.numero)).join(', ') || '—' }}</div>
          <div class="col-12 col-sm-4"><div class="text-caption text-suave">Cadastrado em</div>{{ formatarData(rep.data_cadastro) }}</div>
        </div>
      </section>

      <section v-if="posicao" class="cartao q-pa-md q-mb-md">
        <div class="row items-center">
          <div class="formulario__secao col">Com o representante nesta loja</div>
          <q-btn v-if="sessao.pode('consignacao.transferir') && rep.ativo && !rep.bloqueado" flat no-caps color="primary" icon="move_up" label="Nova transferência" @click="novaTransferencia" />
        </div>
        <div class="row q-col-gutter-md">
          <div class="col-6 col-sm-3"><div class="text-caption text-suave">Peças</div>{{ formatarQuantidade(posicao.pecas) }}</div>
          <div class="col-6 col-sm-3"><div class="text-caption text-suave">Em uso (preço da transferência)</div>{{ formatarMoeda(posicao.em_uso) }}</div>
          <div class="col-6 col-sm-3"><div class="text-caption text-suave">Em uso (preço atual)</div>{{ formatarMoeda(posicao.em_uso_atual) }}</div>
          <div class="col-6 col-sm-3">
            <div class="text-caption text-suave">Resta do limite</div>
            <span :class="Number(posicao.disponivel) < 0 ? 'text-negative' : ''">{{ formatarMoeda(posicao.disponivel) }}</span>
          </div>
        </div>
        <q-expansion-item v-if="posicao.itens.length" dense label="Ver os produtos" class="q-mt-sm">
          <q-markup-table flat dense>
            <thead><tr><th class="text-left">Produto</th><th class="text-right">Qtd.</th><th class="text-right">Preço da transferência</th><th class="text-right">Preço atual</th></tr></thead>
            <tbody>
              <tr v-for="i in posicao.itens" :key="i.produto_id">
                <td>{{ formatarCodigoProduto(i.codigo) }} · {{ i.descricao }}</td>
                <td class="text-right">{{ formatarQuantidade(i.quantidade) }}</td>
                <td class="text-right">{{ formatarMoeda(i.total_transferencia) }}</td>
                <td class="text-right">{{ formatarMoeda(i.total_atual) }}</td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-expansion-item>
      </section>

      <section class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Limite, bloqueio e comissões</div>
        <div class="row q-col-gutter-md">
          <div class="col-12 col-md-5 q-gutter-sm">
            <q-input v-model="limites.limite" outlined dense type="number" min="0" step="0.01" label="Limite (R$, pelo preço da transferência)" :readonly="!podeLimites" />
            <q-toggle v-model="limites.bloqueado" label="Bloqueado" color="negative" :disable="!podeLimites" />
            <div v-if="limites.bloqueado" class="text-caption text-suave">Bloqueado não leva mercadoria nem acerta para si a prazo; devolve e acerta para os clientes dele.</div>
            <q-input v-if="limites.bloqueado" v-model="limites.motivo_bloqueio" outlined dense autogrow label="Motivo do bloqueio *" :readonly="!podeLimites" />
            <q-toggle v-model="limites.bloqueia_impressao" label="Bloquear impressão" :disable="!podeLimites" />
            <q-toggle v-model="limites.bloqueia_devolucao" label="Bloquear devolução" :disable="!podeLimites" />
          </div>
          <div class="col-12 col-md-7">
            <div class="text-caption text-suave q-mb-xs">Comissão por tipo de cobrança e no acerto à vista e de queima (vazio: a padrão)</div>
            <div v-for="c in limites.comissoes" :key="c.tipo_cobranca" class="row items-center q-col-gutter-sm q-mb-xs">
              <div class="col">{{ c.nome }}</div>
              <q-input v-model="c.percentual" outlined dense type="number" min="0" max="100" step="0.01" suffix="%" :placeholder="c.padraoDoTipo" class="col-4" :readonly="!podeLimites" />
            </div>
          </div>
        </div>
        <q-btn v-if="podeLimites" unelevated no-caps color="primary" icon="check" label="Salvar limite e comissões" class="q-mt-sm" :loading="salvando === 'limites'" @click="salvarLimites" />
      </section>

      <section class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Consignado</div>
        <div class="row q-col-gutter-md">
          <q-input v-model="dados.lembrete" outlined dense autogrow label="Lembrete (aparece ao abrir)" class="col-12 col-md-6" :readonly="!podeEditar" />
          <q-input v-model="dados.lembrete_acerto" outlined dense autogrow label="Lembrete do acerto" class="col-12 col-md-6" :readonly="!podeEditar" />
          <q-input v-model="dados.observacao" outlined dense autogrow label="Observação" class="col-12 col-md-6" :readonly="!podeEditar" />
          <q-input v-model="dados.ultima_conferencia" outlined dense type="date" stack-label label="Conferido em" class="col-6 col-md-3" :readonly="!podeEditar" />
          <div class="col-6 col-md-3"><q-toggle v-model="dados.ativo" label="Ativo" :disable="!podeEditar" /></div>
        </div>
        <div class="formulario__secao q-mt-md">Avalista</div>
        <div class="row q-col-gutter-md">
          <q-input v-model="dados.avalista_nome" outlined dense label="Nome" maxlength="100" class="col-12 col-md-6" :readonly="!podeEditar" />
          <q-input v-model="dados.avalista_cpf" outlined dense label="CPF" mask="###.###.###-##" unmasked-value class="col-6 col-md-3" :readonly="!podeEditar" />
          <q-input v-model="dados.avalista_rg" outlined dense label="RG" maxlength="20" class="col-6 col-md-3" :readonly="!podeEditar" />
          <q-input v-model="dados.avalista_endereco" outlined dense label="Endereço" maxlength="200" class="col-12 col-md-6" :readonly="!podeEditar" />
          <q-input v-model="dados.avalista_telefones" outlined dense label="Telefones" maxlength="200" class="col-12 col-md-6" :readonly="!podeEditar" />
          <q-input v-model="dados.avalista_anotacoes" outlined dense autogrow label="Anotações" class="col-12" :readonly="!podeEditar" />
        </div>
        <q-btn v-if="podeEditar" unelevated no-caps color="primary" icon="check" label="Salvar" class="q-mt-sm" :loading="salvando === 'dados'" @click="salvarDados" />
      </section>

      <section v-if="podeEditar" class="cartao q-pa-md q-mb-md">
        <div class="formulario__secao">Senha da transferência</div>
        <div class="text-caption text-suave q-mb-sm">
          O representante confirma a transferência no balcão com ela. {{ rep.tem_senha ? 'Já tem senha: preencha só para trocar.' : 'Ainda não tem senha.' }}
        </div>
        <div class="row q-col-gutter-sm items-center">
          <q-input v-model="senha" outlined dense type="password" autocomplete="new-password" label="Nova senha (4 a 20)" maxlength="20" class="col-12 col-sm-4" />
          <div class="col-auto"><q-btn flat no-caps color="primary" icon="key" label="Trocar a senha" :disable="senha.length < 4" :loading="salvando === 'senha'" @click="trocarSenha" /></div>
        </div>
      </section>
    </template>
  </q-page>
</template>

<script setup>
import { useQuasar } from 'quasar'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, mensagemDeErro } from '@/servicos/api'
import {
  formatarCodigoProduto, formatarDataHora, formatarDocumento, formatarMoeda, formatarQuantidade, formatarTelefone, nomeSetor,
} from '@/servicos/formatos'
import { useSessaoStore } from '@/stores/sessao'

const CAMPOS = ['ativo', 'lembrete', 'lembrete_acerto', 'observacao', 'ultima_conferencia', 'avalista_nome', 'avalista_cpf',
  'avalista_rg', 'avalista_endereco', 'avalista_telefones', 'avalista_anotacoes']

const $q = useQuasar()
const rota = useRoute()
const roteador = useRouter()
const sessao = useSessaoStore()
const posicao = ref(null)
const podeEditar = computed(() => sessao.pode('representantes.editar'))
const podeLimites = computed(() => sessao.pode('representantes.limites'))
const rep = ref(null)
const dados = ref({})
const limites = ref({})
const senha = ref('')
const salvando = ref('')

const endereco = computed(() => {
  const c = rep.value?.cliente
  if (!c) return ''
  return [[c.logradouro, c.numero, c.complemento].filter(Boolean).join(', '), nomeSetor(c.setor), c.cep && `CEP ${c.cep}`].filter(Boolean).join(' - ')
})

function formatarData(valor) {
  return valor ? formatarDataHora(valor).slice(0, 10) : '—'
}

function mostrar(dadosApi) {
  rep.value = dadosApi
  dados.value = Object.fromEntries(CAMPOS.map((c) => [c, dadosApi[c] ?? (c === 'ativo' ? true : '')]))
  limites.value = {
    limite: dadosApi.limite,
    bloqueado: dadosApi.bloqueado,
    motivo_bloqueio: dadosApi.motivo_bloqueio ?? '',
    bloqueia_impressao: dadosApi.bloqueia_impressao,
    bloqueia_devolucao: dadosApi.bloqueia_devolucao,
    comissoes: dadosApi.comissoes.map((c) => ({ ...c, percentual: c.padrao ? '' : c.percentual, padraoDoTipo: String(Number(c.percentual_padrao)) })),
  }
}

async function salvar(qual, acao, mensagem) {
  salvando.value = qual
  try {
    mostrar((await acao()).data)
    $q.notify({ type: 'positive', message: mensagem })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  } finally {
    salvando.value = ''
  }
}

function salvarDados() {
  const corpo = Object.fromEntries(Object.entries(dados.value).map(([k, v]) => [k, v === '' ? null : v]))
  return salvar('dados', () => api.put(`/representantes/${rota.params.id}`, corpo), 'Representante salvo')
}

function salvarLimites() {
  const { comissoes, ...resto } = limites.value
  const corpo = {
    ...resto,
    limite: Number(resto.limite || 0).toFixed(2),
    comissoes: comissoes.filter((c) => c.percentual !== '' && c.percentual !== null).map((c) => ({ tipo_cobranca: c.tipo_cobranca, percentual: String(c.percentual) })),
  }
  return salvar('limites', () => api.put(`/representantes/${rota.params.id}/limites`, corpo), 'Limite e comissões salvos')
}

async function trocarSenha() {
  await salvar('senha', () => api.put(`/representantes/${rota.params.id}/senha`, { senha: senha.value }), 'Senha trocada')
  senha.value = ''
}

async function novaTransferencia() {
  try {
    const { data } = await api.post('/consignacao/transferencias', { representante_id: rep.value.id })
    roteador.push({ name: 'transferencia', params: { id: data.id } })
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
}

onMounted(async () => {
  try {
    const [r, p] = await Promise.all([api.get(`/representantes/${rota.params.id}`), api.get(`/representantes/${rota.params.id}/posicao`)])
    mostrar(r.data)
    posicao.value = p.data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
  }
})
</script>
