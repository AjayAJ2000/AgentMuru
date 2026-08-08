import type { ApprovalStatus, RunStatus, RuntimeEvent, SessionSnapshot } from './protocol'

export interface WorkspaceMessage {
  id: string
  role: 'user' | 'assistant' | 'tool' | 'system'
  content: string
  runId: string | null
  name?: string | null
  streaming?: boolean
}

export interface WorkspaceRun {
  id: string
  agent: string
  status: RunStatus
  errorCode?: string | null
}

export interface ToolActivity {
  id: string
  runId: string | null
  name: string
  status: 'requested' | 'running' | 'completed' | 'failed'
  arguments: Record<string, unknown>
  result?: unknown
  errorCode?: string
}

export interface WorkspaceApproval {
  id: string
  runId: string
  toolCallId: string
  toolName: string
  arguments: Record<string, unknown>
  permission: string | null
  risk: string
  status: ApprovalStatus
  actor?: string
  reason?: string | null
}

export interface WorkspaceArtifact {
  id: string
  runId: string | null
  kind: string
  name: string
  mimeType: string
  creator: string
}

export interface TraceSpan {
  id: string
  parentId: string | null
  name: string
  kind: string
  status: string
  durationMs?: number
}

export interface WorkspaceUsage {
  inputTokens: number
  outputTokens: number
  totalTokens: number
  cost: number
}

export interface WorkspaceState {
  sessionId: string
  title: string | null
  messages: WorkspaceMessage[]
  runs: Record<string, WorkspaceRun>
  activities: ToolActivity[]
  approvals: WorkspaceApproval[]
  artifacts: WorkspaceArtifact[]
  spans: TraceSpan[]
  usage: WorkspaceUsage
  lastSequence: number
  protocolError: string | null
}

export function initialWorkspaceState(sessionId: string): WorkspaceState {
  return {
    sessionId,
    title: null,
    messages: [],
    runs: {},
    activities: [],
    approvals: [],
    artifacts: [],
    spans: [],
    usage: { inputTokens: 0, outputTokens: 0, totalTokens: 0, cost: 0 },
    lastSequence: 0,
    protocolError: null,
  }
}

export function hydrateWorkspace(snapshot: SessionSnapshot): WorkspaceState {
  const state = initialWorkspaceState(snapshot.id)
  state.title = snapshot.title
  state.lastSequence = snapshot.event_sequence
  state.messages = snapshot.messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    runId: null,
    name: message.name,
  }))
  state.runs = Object.fromEntries(snapshot.runs.map((run) => [
    run.id,
    { id: run.id, agent: run.agent_name, status: run.status, errorCode: run.error_code },
  ]))
  state.artifacts = snapshot.artifacts.map((artifact) => ({
    id: artifact.id,
    runId: artifact.run_id,
    kind: artifact.kind,
    name: artifact.name,
    mimeType: artifact.mime_type,
    creator: artifact.creator,
  }))
  state.approvals = snapshot.approvals.map((approval) => ({
    id: approval.id,
    runId: approval.run_id,
    toolCallId: '',
    toolName: approval.tool_name,
    arguments: approval.arguments,
    permission: approval.permission,
    risk: approval.risk,
    status: approval.status,
    reason: approval.reason,
  }))
  return state
}

function stringValue(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}

function numberValue(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function objectValue(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {}
}

function updateActivity(
  activities: ToolActivity[],
  id: string,
  update: Partial<ToolActivity>,
): ToolActivity[] {
  const index = activities.findIndex((activity) => activity.id === id)
  if (index === -1) {
    return [...activities, {
      id,
      runId: null,
      name: stringValue(update.name, 'tool'),
      status: update.status ?? 'requested',
      arguments: update.arguments ?? {},
      ...update,
    }]
  }
  return activities.map((activity, position) => position === index ? { ...activity, ...update } : activity)
}

export function reduceWorkspace(state: WorkspaceState, event: RuntimeEvent): WorkspaceState {
  if (event.session_id !== state.sessionId || event.sequence <= state.lastSequence) return state
  const expected = state.lastSequence + 1
  if (event.sequence !== expected) {
    return { ...state, protocolError: `Expected event sequence ${expected}, received ${event.sequence}` }
  }

  const next: WorkspaceState = { ...state, lastSequence: event.sequence, protocolError: null }
  const payload = event.payload
  const runId = event.run_id

  switch (event.type) {
    case 'session.started':
      return { ...next, title: stringValue(payload.title) || state.title }
    case 'user.message.received':
      return {
        ...next,
        messages: [...state.messages, {
          id: stringValue(payload.message_id, event.id),
          role: 'user',
          content: stringValue(payload.content),
          runId,
        }],
      }
    case 'agent.started': {
      if (!runId) return next
      return {
        ...next,
        runs: {
          ...state.runs,
          [runId]: { id: runId, agent: stringValue(payload.agent, 'agent'), status: 'running' },
        },
      }
    }
    case 'model.token.delta': {
      if (!runId) return next
      const draftId = `assistant-${runId}`
      const existing = state.messages.find((message) => message.id === draftId)
      const messages = existing
        ? state.messages.map((message) => message.id === draftId
          ? { ...message, content: message.content + stringValue(payload.delta), streaming: true }
          : message)
        : [...state.messages, {
          id: draftId,
          role: 'assistant' as const,
          content: stringValue(payload.delta),
          runId,
          streaming: true,
        }]
      return { ...next, messages }
    }
    case 'assistant.message.completed': {
      const draftId = runId ? `assistant-${runId}` : ''
      const finalMessage: WorkspaceMessage = {
        id: stringValue(payload.message_id, event.id),
        role: 'assistant',
        content: stringValue(payload.content),
        runId,
        streaming: false,
      }
      const hasDraft = state.messages.some((message) => message.id === draftId)
      return {
        ...next,
        messages: hasDraft
          ? state.messages.map((message) => message.id === draftId ? finalMessage : message)
          : [...state.messages, finalMessage],
      }
    }
    case 'tool.call.requested': {
      const id = stringValue(payload.tool_call_id, event.id)
      return {
        ...next,
        activities: updateActivity(state.activities, id, {
          id,
          runId,
          name: stringValue(payload.tool_name, 'tool'),
          status: 'requested',
          arguments: objectValue(payload.arguments),
        }),
      }
    }
    case 'tool.call.started':
    case 'tool.call.completed':
    case 'tool.call.failed': {
      const id = stringValue(payload.tool_call_id, event.id)
      const status = event.type.endsWith('started')
        ? 'running'
        : event.type.endsWith('completed') ? 'completed' : 'failed'
      return {
        ...next,
        activities: updateActivity(state.activities, id, {
          runId,
          name: stringValue(payload.tool_name, 'tool'),
          status,
          result: payload.result,
          errorCode: stringValue(payload.code) || undefined,
        }),
      }
    }
    case 'approval.requested':
      return {
        ...next,
        approvals: [...state.approvals, {
          id: stringValue(payload.approval_id, event.id),
          runId: runId ?? '',
          toolCallId: stringValue(payload.tool_call_id),
          toolName: stringValue(payload.tool_name, 'tool'),
          arguments: objectValue(payload.arguments),
          permission: stringValue(payload.permission) || null,
          risk: stringValue(payload.risk, 'unknown'),
          status: 'pending',
        }],
      }
    case 'approval.granted':
    case 'approval.rejected':
    case 'approval.expired': {
      const approvalId = stringValue(payload.approval_id)
      const status: ApprovalStatus = event.type.endsWith('granted')
        ? 'approved'
        : event.type.endsWith('expired') ? 'expired' : 'rejected'
      return {
        ...next,
        approvals: state.approvals.map((approval) => approval.id === approvalId
          ? { ...approval, status, actor: stringValue(payload.actor), reason: stringValue(payload.reason) || null }
          : approval),
      }
    }
    case 'artifact.created':
      return {
        ...next,
        artifacts: [...state.artifacts, {
          id: stringValue(payload.artifact_id, event.id),
          runId,
          kind: stringValue(payload.kind, 'file'),
          name: stringValue(payload.name, 'Artifact'),
          mimeType: stringValue(payload.mime_type, 'application/octet-stream'),
          creator: stringValue(payload.creator, 'agent'),
        }],
      }
    case 'trace.span.started':
      return {
        ...next,
        spans: [...state.spans, {
          id: stringValue(payload.span_id, event.id),
          parentId: event.parent_id,
          name: stringValue(payload.name, 'span'),
          kind: stringValue(payload.kind, 'runtime'),
          status: 'running',
        }],
      }
    case 'trace.span.completed': {
      const spanId = stringValue(payload.span_id)
      return {
        ...next,
        spans: state.spans.map((span) => span.id === spanId
          ? { ...span, status: stringValue(payload.status, 'completed'), durationMs: numberValue(payload.duration_ms) }
          : span),
      }
    }
    case 'usage.recorded':
      return {
        ...next,
        usage: {
          inputTokens: state.usage.inputTokens + numberValue(payload.input_tokens),
          outputTokens: state.usage.outputTokens + numberValue(payload.output_tokens),
          totalTokens: state.usage.totalTokens + numberValue(payload.total_tokens),
          cost: state.usage.cost + numberValue(payload.cost),
        },
      }
    case 'run.completed':
    case 'run.failed':
    case 'run.cancelled': {
      if (!runId) return next
      const status: RunStatus = event.type === 'run.completed'
        ? 'completed' : event.type === 'run.failed' ? 'failed' : 'cancelled'
      return {
        ...next,
        runs: {
          ...state.runs,
          [runId]: {
            ...(state.runs[runId] ?? { id: runId, agent: 'agent' }),
            status,
            errorCode: stringValue(payload.code) || undefined,
          },
        },
      }
    }
    default:
      return next
  }
}
