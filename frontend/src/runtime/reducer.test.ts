import { describe, expect, it } from 'vitest'
import { initialWorkspaceState, reduceWorkspace } from './reducer'
import type { RuntimeEvent } from './protocol'

function event(
  sequence: number,
  type: string,
  payload: Record<string, unknown> = {},
  runId: string | null = 'run-1',
): RuntimeEvent {
  return {
    id: `event-${sequence}`,
    type,
    timestamp: '2026-08-08T00:00:00Z',
    session_id: 'session-1',
    sequence,
    run_id: runId,
    trace_id: 'trace-1',
    parent_id: null,
    payload,
  }
}

describe('reduceWorkspace', () => {
  it('projects messages and streaming deltas without duplicating replayed events', () => {
    let state = initialWorkspaceState('session-1')
    state = reduceWorkspace(state, event(1, 'session.started', { title: 'Research' }, null))
    state = reduceWorkspace(state, event(2, 'user.message.received', { message_id: 'u-1', content: 'Hello' }))
    state = reduceWorkspace(state, event(3, 'agent.started', { agent: 'researcher' }))
    state = reduceWorkspace(state, event(4, 'model.token.delta', { delta: 'Hel' }))
    state = reduceWorkspace(state, event(5, 'model.token.delta', { delta: 'lo' }))
    state = reduceWorkspace(state, event(5, 'model.token.delta', { delta: 'lo' }))

    expect(state.title).toBe('Research')
    expect(state.messages.map((message) => message.content)).toEqual(['Hello', 'Hello'])
    expect(state.messages[1].streaming).toBe(true)
    expect(state.lastSequence).toBe(5)
  })

  it('tracks tools approvals artifacts usage and terminal run state', () => {
    let state = initialWorkspaceState('session-1')
    state = reduceWorkspace(state, event(1, 'tool.call.requested', { tool_call_id: 'call-1', tool_name: 'query', arguments: { sql: 'select 1' } }))
    state = reduceWorkspace(state, event(2, 'approval.requested', { approval_id: 'approval-1', tool_call_id: 'call-1', tool_name: 'query', arguments: {}, permission: 'database.write', risk: 'high' }))
    state = reduceWorkspace(state, event(3, 'approval.granted', { approval_id: 'approval-1', actor: 'alice' }))
    state = reduceWorkspace(state, event(4, 'tool.call.completed', { tool_call_id: 'call-1', tool_name: 'query', result: { rows: 1 } }))
    state = reduceWorkspace(state, event(5, 'artifact.created', { artifact_id: 'artifact-1', kind: 'table', name: 'result', mime_type: 'application/json', creator: 'query' }))
    state = reduceWorkspace(state, event(6, 'usage.recorded', { input_tokens: 5, output_tokens: 3, total_tokens: 8, cost: 0.01 }))
    state = reduceWorkspace(state, event(7, 'run.completed', { status: 'completed' }))

    expect(state.activities[0].status).toBe('completed')
    expect(state.approvals[0].status).toBe('approved')
    expect(state.artifacts[0].name).toBe('result')
    expect(state.usage).toEqual({ inputTokens: 5, outputTokens: 3, totalTokens: 8, cost: 0.01 })
    expect(state.runs['run-1'].status).toBe('completed')
  })

  it('flags sequence gaps so the client can request a snapshot', () => {
    const state = reduceWorkspace(initialWorkspaceState('session-1'), event(2, 'agent.started'))

    expect(state.protocolError).toContain('Expected event sequence 1')
    expect(state.lastSequence).toBe(0)
  })
})
