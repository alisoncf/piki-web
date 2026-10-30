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
