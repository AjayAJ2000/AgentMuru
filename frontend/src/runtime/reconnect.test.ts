import { describe, expect, it, vi } from 'vitest'

import { createReconnectController, reconnectDelay } from './reconnect'

describe('reconnect policy', () => {
  it('uses bounded exponential delays', () => {
    expect([0, 1, 2, 3, 4, 5, 8].map(reconnectDelay)).toEqual([
      500,
      1000,
      2000,
      4000,
      8000,
      10000,
      10000,
    ])
  })

  it('allows one timer, resets after open, and stops after disposal', () => {
    const connect = vi.fn()
    const callbacks = new Map<number, () => void>()
    const delays: number[] = []
    let nextTimerId = 0
    const schedule = vi.fn((callback: () => void, delay: number) => {
      const timerId = ++nextTimerId
      callbacks.set(timerId, callback)
      delays.push(delay)
      return timerId
    })
    const cancel = vi.fn((timerId: number) => callbacks.delete(timerId))
    const controller = createReconnectController(connect, schedule, cancel)

    controller.closed()
    controller.closed()
    expect(delays).toEqual([500])
    expect(callbacks.size).toBe(1)

    const firstCallback = callbacks.get(1)
    callbacks.delete(1)
    firstCallback?.()
    expect(connect).toHaveBeenCalledTimes(1)

    controller.closed()
    expect(delays).toEqual([500, 1000])
    controller.opened()
    expect(callbacks.size).toBe(0)

    controller.closed()
    expect(delays).toEqual([500, 1000, 500])
    controller.dispose()
    controller.closed()

    expect(callbacks.size).toBe(0)
    expect(delays).toEqual([500, 1000, 500])
    expect(cancel).toHaveBeenCalledTimes(2)
  })
})
