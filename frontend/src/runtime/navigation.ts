export type NavigationSource = 'user' | 'popstate'

export function navigationAction(path: string, source: NavigationSource) {
  return {
    message: { type: 'navigate' as const, path },
    history: source === 'user' ? 'push' as const : 'none' as const,
  }
}
