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

// tipos de documento do crediário (mesmos códigos da API, TIPOS_DE_DOCUMENTO em clientes/servico.py)
export const TIPOS_DOCUMENTO = [
  { value: 'identidade', label: 'Identidade (RG ou CNH)' },
  { value: 'cpf', label: 'CPF' },
  { value: 'endereco', label: 'Comprovante de endereço' },
  { value: 'renda', label: 'Comprovante de renda' },
  { value: 'contrato', label: 'Ficha ou contrato de crediário assinado' },
  { value: 'foto', label: 'Foto do cliente' },
  { value: 'outro', label: 'Outro' },
]

export function nomeTipoDocumento(tipo) {
  return TIPOS_DOCUMENTO.find((t) => t.value === tipo)?.label ?? tipo
}

/** Tamanho de arquivo para exibir: 312 KB, 1,4 MB. */
export function formatarTamanho(bytes) {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} MB`
}

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

/** Valor em reais da API ("1234.5") para exibir: R$ 1.234,50. Vazio fica vazio. */
export function formatarMoeda(valor) {
  if (valor === null || valor === undefined || valor === '') return ''
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

/** Código do produto como sai no código de barras interno: 00012345. */
export function formatarCodigoProduto(codigo) {
  return String(codigo ?? '').padStart(8, '0')
}

/** Origem da mercadoria na NF-e. */
export const ORIGENS = [
  { value: 0, label: '0 - Nacional' },
  { value: 1, label: '1 - Estrangeira, importação direta' },
  { value: 2, label: '2 - Estrangeira, comprada no mercado interno' },
  { value: 3, label: '3 - Nacional, com mais de 40% de conteúdo importado' },
  { value: 4, label: '4 - Nacional, produzida conforme processos básicos' },
  { value: 5, label: '5 - Nacional, com até 40% de conteúdo importado' },
  { value: 6, label: '6 - Estrangeira, importação direta, sem similar nacional' },
  { value: 7, label: '7 - Estrangeira, mercado interno, sem similar nacional' },
  { value: 8, label: '8 - Nacional, com mais de 70% de conteúdo importado' },
]

/** Quantidade da API ("12.000", "-2.500") para exibir: 12, -2,5. */
export function formatarQuantidade(valor) {
  if (valor === null || valor === undefined || valor === '') return ''
  return Number(valor).toLocaleString('pt-BR', { maximumFractionDigits: 3 })
}
