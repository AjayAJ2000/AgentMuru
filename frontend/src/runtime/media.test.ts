import { describe, expect, it } from 'vitest'

import { safeMediaUrl } from './media'


describe('safeMediaUrl', () => {
  it.each([
    ['/__brickflow_asset__/logo/mark.svg', 'https://app.example.com/__brickflow_asset__/logo/mark.svg'],
    ['assets/loading.webm', 'https://app.example.com/dashboard/assets/loading.webm'],
    ['https://cdn.example.com/loading.svg', 'https://cdn.example.com/loading.svg'],
    ['  http://cdn.example.com/loading.svg  ', 'http://cdn.example.com/loading.svg'],
  ])('allows browser-safe local and HTTP(S) media URLs', (input, expected) => {
    expect(safeMediaUrl(input, 'https://app.example.com/dashboard/')).toBe(expected)
  })

  it.each([
    'javascript:alert(1)',
    'data:image/svg+xml,<svg onload=alert(1)>',
    'file:///etc/passwd',
    'vbscript:msgbox(1)',
  ])('rejects executable or local-file URL schemes', (input) => {
    expect(safeMediaUrl(input, 'https://app.example.com/dashboard/')).toBeUndefined()
  })
})
