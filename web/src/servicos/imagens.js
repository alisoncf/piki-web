/**
 * Reduz uma foto antes de enviar: o lado maior fica com até `lado` pixels, em
 * JPEG. Uma foto de celular (3 a 5 MB) vira uns 300 KB e continua legível.
 * PDF, ou imagem que o navegador não consegue abrir, vai como veio.
 */
export async function reduzirImagem(arquivo, { lado = 1600, qualidade = 0.85 } = {}) {
  if (!arquivo.type.startsWith('image/')) return arquivo
  let imagem
  try {
    imagem = await createImageBitmap(arquivo, { imageOrientation: 'from-image' })
  } catch {
    return arquivo
  }
  const escala = Math.min(1, lado / Math.max(imagem.width, imagem.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(imagem.width * escala)
  canvas.height = Math.round(imagem.height * escala)
  canvas.getContext('2d').drawImage(imagem, 0, 0, canvas.width, canvas.height)
  imagem.close()
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', qualidade))
  if (!blob) return arquivo
  const nome = arquivo.name.replace(/\.[^.]*$/, '') + '.jpg'
  return new File([blob], nome, { type: 'image/jpeg' })
}
