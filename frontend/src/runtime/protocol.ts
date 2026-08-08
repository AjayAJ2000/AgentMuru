export const PROTOCOL_VERSION = 1 as const

export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue }

export interface RuntimeEvent {
  id: string
  type: string
  timestamp: string
  session_id: string
  sequence: number
  run_id: string | null
  trace_id: string | null
  parent_id: string | null
  payload: Record<string, unknown>
}

export interface ProtocolEnvelope {
  protocol_version: number
  kind: 'event' | 'error' | 'pong'
  data: RuntimeEvent | Record<string, unknown>
}

export type ConnectionState = 'connecting' | 'connected' | 'reconnecting' | 'offline' | 'error'

export interface SessionSummary {
  id: string
  title: string | null
  updatedAt: string
  eventSequence: number
}

export interface SessionSnapshot {
  id: string
  title: string | null
  updated_at: string
  event_sequence: number
  messages: Array<{
    id: string
    role: 'user' | 'assistant' | 'tool' | 'system'
    content: string
    name: string | null
    tool_call_id: string | null
  }>
  runs: Array<{
    id: string
    agent_name: string
    status: RunStatus
    error_code: string | null
  }>
  artifacts: Array<{
    id: string
    run_id: string | null
    kind: string
    name: string
    mime_type: string
    creator: string
  }>
  approvals: Array<{
    id: string
    run_id: string
    tool_name: string
    arguments: Record<string, unknown>
    permission: string | null
    risk: string
    status: ApprovalStatus
    reason: string | null
  }>
}

export type RunStatus = 'queued' | 'running' | 'waiting_approval' | 'completed' | 'failed' | 'cancelled'
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired'
