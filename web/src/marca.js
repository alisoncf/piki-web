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

/**
 * Mostra em que empresa o usuário está: a cor dela vai para a variável
 * --piki-empresa (faixa do cabeçalho e menu) e o nome vai para a aba do navegador.
 */
export function aplicarEmpresa(empresa, doc = document) {
  if (empresa?.cor) doc.documentElement.style.setProperty('--piki-empresa', empresa.cor)
  else doc.documentElement.style.removeProperty('--piki-empresa')
  doc.title = empresa ? `${empresa.nome} · ${SISTEMA.nome}` : SISTEMA.nome
}
