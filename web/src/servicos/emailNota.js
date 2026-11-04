import { api, mensagemDeErro } from '@/servicos/api'

/**
 * Manda o DANFE e o XML da nota por e-mail (D29), pela conta do sistema: pergunta para quem, já com o e-mail do
 * cliente. Em homologação vai sempre para a própria conta do sistema, e a tela só avisa.
 */
export async function enviarNotaPorEmail($q, nota) {
  let sugerido
  try {
    sugerido = (await api.get(`/notas/${nota.id}/email`)).data
  } catch (e) {
    $q.notify({ type: 'negative', message: mensagemDeErro(e) })
    return
  }
  const opcoes = sugerido.homologacao
    ? { message: `Em homologação, o e-mail vai sempre para a conta do sistema (${sugerido.para ?? 'não configurada'}).` }
    : {
        message: 'Para quem mandar o DANFE e o XML?',
        prompt: { model: sugerido.para ?? '', type: 'email', isValid: (v) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v.trim()) },
      }
  $q.dialog({ title: 'Enviar por e-mail', ...opcoes, cancel: { flat: true, label: 'Voltar' }, ok: { label: 'Enviar' } }).onOk(async (para) => {
    try {
      const enviado = (await api.post(`/notas/${nota.id}/email`, { para: typeof para === 'string' ? para.trim() : null })).data
      $q.notify({ type: 'positive', message: `E-mail enviado para ${enviado.para}` })
    } catch (e) {
      $q.notify({ type: 'negative', message: mensagemDeErro(e), timeout: 8000 })
    }
  })
}
