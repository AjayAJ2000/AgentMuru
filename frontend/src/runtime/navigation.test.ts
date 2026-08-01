import { describe, expect, it } from 'vitest'
import { navigationAction } from './navigation'

describe('navigationAction', () => {
  it('pushes history only for user navigation', () => {
    expect(navigationAction('/reports?period=week#summary', 'user')).toEqual({
      message: { type: 'navigate', path: '/reports?period=week#summary' },
      history: 'push',
    })
    expect(navigationAction('/home', 'popstate').history).toBe('none')
  })
})
