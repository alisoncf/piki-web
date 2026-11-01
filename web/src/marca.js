/**
 * Marca exibida no sistema: a loja (quem usa) e o Piki (o sistema).
 * Os arquivos ficam em public/. As cores estão em css/quasar.variables.scss.
 */
export const LOJA = {
  nome: 'Requinte',
  complemento: 'Enxovais',
  logo: '/requinte-logo.svg',
}

export const SISTEMA = {
  nome: 'Piki',
  icone: '/piki-icone.svg',
}

// cada cor do esquema da empresa (D19) e a variável do CSS (css/app.css) que ela muda
const VARIAVEIS = { principal: '--piki-empresa', fundo: '--piki-fundo', menu: '--piki-menu-fundo' }

/**
 * Mostra em que empresa o usuário está: o esquema de cores dela vai para as
 * variáveis do CSS (faixa do cabeçalho, fundo das telas, menu) e o nome vai para
 * a aba do navegador. Sem empresa, valem as cores da marca.
 */
export function aplicarEmpresa(empresa, doc = document) {
  for (const [cor, variavel] of Object.entries(VARIAVEIS)) {
    const valor = empresa?.tema?.[cor]
    if (valor) doc.documentElement.style.setProperty(variavel, valor)
    else doc.documentElement.style.removeProperty(variavel)
  }
  doc.title = empresa ? `${empresa.nome} · ${SISTEMA.nome}` : SISTEMA.nome
}
