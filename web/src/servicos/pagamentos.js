// contas do que o cliente paga no caixa (venda ou crediário), em centavos para não errar no arredondamento

export const centavos = (valor) => Math.round(Number(valor || 0) * 100)

/** Soma dos valores lançados, em reais. */
export function somar(pagamentos) {
  return pagamentos.reduce((soma, pg) => soma + centavos(pg.valor), 0) / 100
}

/** Quanto foi lançado no dinheiro, em reais. */
export function noDinheiro(pagamentos, formas) {
  return somar(pagamentos.filter((pg) => formas.find((f) => f.id === pg.forma_pagamento_id)?.tipo === 'dinheiro'))
}

/** O troco: o que o cliente deu menos o que ficou no dinheiro (0 enquanto não informou). */
export function troco(valorRecebido, dinheiro) {
  return dinheiro && valorRecebido ? (centavos(valorRecebido) - centavos(dinheiro)) / 100 : 0
}

/** Uma linha nova: a primeira forma ainda não usada, já com o que falta lançar. */
export function novaLinha(pagamentos, formas, falta) {
  const usadas = new Set(pagamentos.map((pg) => pg.forma_pagamento_id))
  const sugerida = formas.find((f) => !usadas.has(f.id)) ?? formas[0]
  return { forma_pagamento_id: sugerida?.id ?? null, valor: falta > 0 ? falta.toFixed(2) : '', parcelas: 1 }
}

/** Todas as linhas têm forma e valor, e o dinheiro dado cobre o que ficou no dinheiro. */
export function completos(pagamentos, valorRecebido, dinheiro) {
  if (pagamentos.some((pg) => !pg.forma_pagamento_id || !(Number(pg.valor) > 0))) return false
  return !(dinheiro && valorRecebido && troco(valorRecebido, dinheiro) < 0)
}
