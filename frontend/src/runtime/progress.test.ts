import { describe, expect, it } from 'vitest'

import { progressColor } from './progress'

describe('progressColor', () => {
  it('maps the default blue color to the primary theme token', () => {
    expect(progressColor('blue')).toBe('var(--db-primary)')
  })

  it('maps friendly status colors to defined theme tokens', () => {
    expect(progressColor('green')).toBe('var(--db-success)')
    expect(progressColor('orange')).toBe('var(--db-warning)')
    expect(progressColor('red')).toBe('var(--db-error)')
  })

  it('preserves explicit CSS colors and safely falls back for unknown names', () => {
    expect(progressColor('#2563eb')).toBe('#2563eb')
    expect(progressColor('var(--custom-progress)')).toBe('var(--custom-progress)')
    expect(progressColor('not-a-theme-color')).toBe('var(--db-primary)')
  })
})
