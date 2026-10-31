/** Formatação de documentos e telefones para exibir. A API guarda só os dígitos. */

// mesmos códigos da API (app/nucleo/documentos.py) e do VB6
export const TIPOS_TELEFONE = [
  { value: '3', label: 'Celular' },
  { value: '1', label: 'Residencial' },
  { value: '2', label: 'Comercial' },
  { value: '4', label: 'Recado' },
  { value: '5', label: 'Fax' },
]

export function soDigitos(valor) {
  return String(valor ?? '').replace(/\D/g, '')
}

export function formatarCpf(cpf) {
  const d = soDigitos(cpf)
  return d.length === 11 ? d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4') : d
}

export function formatarTelefone(numero) {
  const d = soDigitos(numero)
  if (d.length === 11) return d.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3')
  if (d.length === 10) return d.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3')
  return d
}

export function nomeTipoTelefone(tipo) {
  return TIPOS_TELEFONE.find((t) => t.value === tipo)?.label ?? tipo
}

/** Máscara do campo de telefone: 9 dígitos depois do DDD para celular, 8 para fixo. */
export function mascaraTelefone(numero) {
  return soDigitos(numero).length > 10 ? '(##) #####-####' : '(##) ####-#####'
}

export function formatarCnpj(cnpj) {
  const d = soDigitos(cnpj)
  return d.length === 14 ? d.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5') : d
}

export function formatarDocumento(documento) {
  return soDigitos(documento).length === 14 ? formatarCnpj(documento) : formatarCpf(documento)
}

// mesmos nomes da API (app/dominios/clientes/esquemas.py)
export const FORMAS_COBRANCA = [
  { value: 'domicilio', label: 'Em domicílio' },
  { value: 'trabalho', label: 'No trabalho' },
  { value: 'loja', label: 'Pagamento na loja' },
]

/** Data e hora da API (sem fuso) para exibir: 27/10/2021 15:49. */
export function formatarDataHora(valor) {
  if (!valor) return ''
  const [data, hora = ''] = String(valor).split('T')
  const [ano, mes, dia] = data.split('-')
  return `${dia}/${mes}/${ano}${hora ? ' ' + hora.slice(0, 5) : ''}`
}

/** Para comparar nomes: sem acentos e em minúsculas. */
export function semAcentos(texto) {
  return String(texto ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

/** Setor com a sua cidade: "Jundiaí (Anápolis - GO)". */
export function nomeSetor(setor) {
  return setor ? (setor.cidade ? `${setor.nome} (${setor.cidade.nome} - ${setor.cidade.uf})` : setor.nome) : ''
}
