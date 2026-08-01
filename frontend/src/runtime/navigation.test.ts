import { describe, expect, it } from 'vitest'

import { navigationAction } from './navigation'

describe('navigationAction', () => {
  it('pushes history for user navigation', () => {
    expect(navigationAction('/reports?status=open#latest', 'user', '/')).toEqual({
      message: { type: 'navigate', path: '/reports?status=open#latest' },
      history: 'push',
    })
  })

  it('does not mutate history for popstate synchronization', () => {
    expect(navigationAction('/home', 'popstate', '/home')).toEqual({
      message: { type: 'navigate', path: '/home' },
      history: 'none',
    })
  })

  it('does not push a duplicate entry for the current path', () => {
    expect(navigationAction('/analytics', 'user', '/analytics').history).toBe('none')
  })
})
