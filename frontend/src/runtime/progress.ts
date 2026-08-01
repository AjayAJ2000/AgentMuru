export function progressColor(color?: string): string {
  const candidate = String(color || 'primary').trim()
  const normalized = candidate.toLowerCase()
  const themeColors: Record<string, string> = {
    primary: 'primary',
    blue: 'primary',
    success: 'success',
    green: 'success',
    warning: 'warning',
    orange: 'warning',
    yellow: 'warning',
    error: 'error',
    red: 'error',
    info: 'info',
  }
  const token = themeColors[normalized]
  if (token) return `var(--db-${token})`
  if (/^(#|var\(|rgb\(|rgba\(|hsl\(|hsla\(|oklch\(|color\()/i.test(candidate)) {
    return candidate
  }
  return 'var(--db-primary)'
}
