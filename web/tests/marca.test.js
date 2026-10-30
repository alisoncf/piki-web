import { describe, expect, it } from 'vitest'

import { aplicarEmpresa } from '@/marca'

describe('identificação da empresa ativa', () => {
  it('aplica a cor da empresa e põe o nome na aba', () => {
    aplicarEmpresa({ id: 1, codigo: '01', nome: 'MATRIZ', cor: '#2f6fb0' })
    expect(document.documentElement.style.getPropertyValue('--piki-empresa')).toBe('#2f6fb0')
    expect(document.title).toBe('MATRIZ · Piki')
  })

  it('sem empresa, volta para a cor da marca e o título padrão', () => {
    aplicarEmpresa({ id: 1, codigo: '01', nome: 'MATRIZ', cor: '#2f6fb0' })
    aplicarEmpresa(null)
    expect(document.documentElement.style.getPropertyValue('--piki-empresa')).toBe('')
    expect(document.title).toBe('Piki')
  })
})
