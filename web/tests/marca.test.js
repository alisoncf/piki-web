import { describe, expect, it } from 'vitest'

import { aplicarEmpresa } from '@/marca'
import { misturar, temaDaCor } from '@/servicos/tema'

const MATRIZ = { id: 1, codigo: '01', nome: 'MATRIZ', tema: { principal: '#2f6fb0', fundo: '#eef3f9', menu: '#1f2835' } }

function variavel(nome) {
  return document.documentElement.style.getPropertyValue(nome)
}

describe('identificação da empresa ativa', () => {
  it('aplica o esquema de cores da empresa e põe o nome na aba', () => {
    aplicarEmpresa(MATRIZ)
    expect([variavel('--piki-empresa'), variavel('--piki-fundo'), variavel('--piki-menu-fundo')])
      .toEqual(['#2f6fb0', '#eef3f9', '#1f2835'])
    expect(document.title).toBe('MATRIZ · Piki')
  })

  it('sem empresa, volta para as cores da marca e o título padrão', () => {
    aplicarEmpresa(MATRIZ)
    aplicarEmpresa(null)
    expect([variavel('--piki-empresa'), variavel('--piki-fundo'), variavel('--piki-menu-fundo')]).toEqual(['', '', ''])
    expect(document.title).toBe('Piki')
  })

  it('gera fundo e menu a partir da cor principal, com a mesma conta da API', () => {
    expect(misturar('#000000', '#ffffff', 0.5)).toBe('#808080')
    expect(temaDaCor('#2F6FB0')).toEqual(MATRIZ.tema) // ver api/tests/test_empresas.py
  })
})
