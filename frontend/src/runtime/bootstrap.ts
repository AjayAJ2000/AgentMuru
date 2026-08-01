export function parseBootstrapData<T>(serialized: string | null, fallback: T): T {
  if (!serialized) return fallback
  try {
    return JSON.parse(serialized) as T
  } catch {
    return fallback
  }
}
