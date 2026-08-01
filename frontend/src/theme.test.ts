import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const themeCss = readFileSync(new URL('./theme.css', import.meta.url), 'utf8')

describe('responsive theme safeguards', () => {
  it('allows every responsive grid track and child to shrink within the viewport', () => {
    expect(themeCss).toMatch(/@media \(min-width: 0px\)\s*{\s*\.bf-grid\s*{\s*grid-template-columns:\s*minmax\(0, 1fr\)/)
    expect(themeCss).toMatch(/@media \(min-width: 640px\)\s*{\s*\.bf-grid\s*{\s*grid-template-columns:\s*repeat\(2, minmax\(0, 1fr\)\)/)
    expect(themeCss).toMatch(/@media \(min-width: 1024px\)\s*{\s*\.bf-grid\s*{\s*grid-template-columns:\s*repeat\(var\(--cols, 2\), minmax\(0, 1fr\)\)/)
    expect(themeCss).toMatch(/\.bf-grid\s*>\s*\*\s*,\s*\.bf-card\s*{[^}]*min-width:\s*0/)
  })

  it('honors reduced motion without hiding animated content', () => {
    const reducedMotion = themeCss.match(/@media \(prefers-reduced-motion: reduce\)\s*{([\s\S]*?)\n}/)?.[1]

    expect(reducedMotion).toBeDefined()
    expect(reducedMotion).toContain('animation-duration: 0.01ms !important')
    expect(reducedMotion).toContain('animation-iteration-count: 1 !important')
    expect(reducedMotion).toContain('transition-duration: 0.01ms !important')
    expect(reducedMotion).toContain('scroll-behavior: auto !important')
    expect(reducedMotion).not.toContain('display: none')
    expect(reducedMotion).not.toContain('visibility: hidden')
  })
})
