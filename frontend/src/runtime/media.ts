export function safeMediaUrl(
  value: string | null | undefined,
  baseUrl = 'http://localhost/',
): string | undefined {
  if (typeof value !== 'string') return undefined

  const candidate = value.trim()
  if (!candidate) return undefined

  try {
    const parsed = new URL(candidate, baseUrl)
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return undefined
    return parsed.href
  } catch {
    return undefined
  }
}
