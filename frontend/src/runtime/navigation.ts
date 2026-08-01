import type { ClientNavigate } from '../types'

export type NavigationSource = 'user' | 'popstate'

export function navigationAction(path: string, source: NavigationSource, currentPath: string): {
  message: ClientNavigate
  history: 'push' | 'none'
} {
  return {
    message: { type: 'navigate', path },
    history: source === 'user' && path !== currentPath ? 'push' : 'none',
  }
}
