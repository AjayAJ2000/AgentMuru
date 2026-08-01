type TimerId = ReturnType<typeof setTimeout>
type Schedule = (callback: () => void, delay: number) => TimerId
type Cancel = (timer: TimerId) => void

export function reconnectDelay(attempt: number): number {
  return Math.min(500 * (2 ** Math.max(0, attempt)), 10_000)
}

export function createReconnectController(
  connect: () => void,
  schedule: Schedule = setTimeout,
  cancel: Cancel = clearTimeout,
) {
  let attempt = 0
  let timer: TimerId | null = null
  let disposed = false

  const cancelPending = () => {
    if (timer !== null) cancel(timer)
    timer = null
  }

  return {
    opened() {
      attempt = 0
      cancelPending()
    },
    closed() {
      if (disposed || timer !== null) return
      const delay = reconnectDelay(attempt++)
      const scheduledTimer = schedule(() => {
        if (timer !== scheduledTimer) return
        timer = null
        if (!disposed) connect()
      }, delay)
      timer = scheduledTimer
    },
    dispose() {
      disposed = true
      cancelPending()
    },
  }
}
