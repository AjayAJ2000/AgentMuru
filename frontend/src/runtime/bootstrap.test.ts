import { describe, expect, it } from 'vitest'

import { parseBootstrapData } from './bootstrap'

describe('parseBootstrapData', () => {
  it('parses a valid JSON data block', () => {
    expect(parseBootstrapData('{"title":"Safe"}', { title: 'Fallback' })).toEqual({ title: 'Safe' })
  })

  it('returns the fallback for absent or invalid data', () => {
    const fallback = { title: 'Fallback' }
    expect(parseBootstrapData(null, fallback)).toBe(fallback)
    expect(parseBootstrapData('</script>', fallback)).toBe(fallback)
  })
})
