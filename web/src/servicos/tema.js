/**
 * Esquema de cores da empresa (D19): principal (faixa do cabeçalho e selo),
 * fundo (fundo das telas) e menu (fundo do menu lateral). A mesma conta está
 * na API, em app/dominios/empresas/tema.py.
 */

/** `proporcao` de `cor` com o resto de `outra` (como o color-mix do CSS, em sRGB). */
export function misturar(cor, outra, proporcao) {
  const canais = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16))
  const b = canais(outra)
  return '#' + canais(cor)
    .map((x, i) => Math.round(x * proporcao + b[i] * (1 - proporcao)).toString(16).padStart(2, '0'))
    .join('')
}

/** Fundo das telas bem claro e menu grafite, os dois puxados para a cor principal. */
export function temaDaCor(principal) {
  const cor = principal.toLowerCase()
  return { principal: cor, fundo: misturar(cor, '#ffffff', 0.08), menu: misturar(cor, '#1c1b1f', 0.15) }
}

