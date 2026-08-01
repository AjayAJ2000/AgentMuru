export function shouldSubmitChatInput(key: string, isComposing: boolean): boolean {
  return key === 'Enter' && !isComposing
}

export function chatBlockingEvents(): string[] {
  return ['submit']
}
