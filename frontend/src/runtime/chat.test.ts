import { describe, expect, it } from 'vitest'
import { shouldSubmitChatInput } from './chat'

describe('shouldSubmitChatInput', () => {
  it('submits Enter only outside IME composition', () => {
    expect(shouldSubmitChatInput('Enter', false)).toBe(true)
    expect(shouldSubmitChatInput('Enter', true)).toBe(false)
    expect(shouldSubmitChatInput('a', false)).toBe(false)
  })
})
