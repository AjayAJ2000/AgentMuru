import { PROTOCOL_VERSION, type ConnectionState, type ProtocolEnvelope, type RuntimeEvent, type SessionSnapshot, type SessionSummary } from './protocol'

export interface AppMetadata {
  title: string
  description: string
  primary_agent: string
}

export class RuntimeClient {
  private socket: WebSocket | null = null
  private reconnectTimer: number | null = null
  private closed = false

  private async json<T>(url: string, init?: RequestInit): Promise<T> {
    const response = await fetch(url, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({})) as { detail?: string }
      throw new Error(body.detail ?? `Runtime request failed with ${response.status}`)
    }
    return response.json() as Promise<T>
  }

  app(): Promise<AppMetadata> {
    return this.json('/api/v1/app')
  }

  async sessions(): Promise<SessionSummary[]> {
    const value = await this.json<{ sessions: Array<{ id: string; title: string | null; updated_at: string; event_sequence: number }> }>('/api/v1/sessions')
    return value.sessions.map((session) => ({
      id: session.id,
      title: session.title,
      updatedAt: session.updated_at,
      eventSequence: session.event_sequence,
    }))
  }

  createSession(title?: string): Promise<SessionSnapshot> {
    return this.json('/api/v1/sessions', { method: 'POST', body: JSON.stringify({ title }) })
  }

  session(id: string): Promise<SessionSnapshot> {
    return this.json(`/api/v1/sessions/${encodeURIComponent(id)}`)
  }

  submit(sessionId: string, content: string): Promise<unknown> {
    return this.json(`/api/v1/sessions/${encodeURIComponent(sessionId)}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, idempotency_key: crypto.randomUUID() }),
    })
  }

  cancel(runId: string): Promise<unknown> {
    return this.json(`/api/v1/runs/${encodeURIComponent(runId)}/cancel`, { method: 'POST' })
  }

  decide(approvalId: string, decision: 'approve' | 'reject', reason?: string): Promise<unknown> {
    return this.json(`/api/v1/approvals/${encodeURIComponent(approvalId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ decision, reason }),
    })
  }

  connect(
    sessionId: string,
    after: number,
    onEvent: (event: RuntimeEvent) => void,
    onState: (state: ConnectionState) => void,
    onError: (message: string) => void,
  ): () => void {
    this.disconnect()
    this.closed = false
    let lastSequence = after
    let attempts = 0

    const open = () => {
      onState(attempts === 0 ? 'connecting' : 'reconnecting')
      const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const socket = new WebSocket(
        `${scheme}://${window.location.host}/api/v1/sessions/${encodeURIComponent(sessionId)}/stream?after=${lastSequence}`,
      )
      this.socket = socket
      socket.onopen = () => {
        attempts = 0
        onState('connected')
      }
      socket.onmessage = (message) => {
        try {
          const envelope = JSON.parse(String(message.data)) as ProtocolEnvelope
          if (envelope.protocol_version !== PROTOCOL_VERSION) throw new Error('Unsupported runtime protocol')
          if (envelope.kind === 'event') {
            const event = envelope.data as unknown as RuntimeEvent
            lastSequence = Math.max(lastSequence, event.sequence)
            onEvent(event)
          } else if (envelope.kind === 'error') {
            onError(String((envelope.data as Record<string, unknown>).code ?? 'Runtime stream error'))
          }
        } catch (error) {
          onError(error instanceof Error ? error.message : 'Invalid runtime event')
        }
      }
      socket.onerror = () => socket.close()
      socket.onclose = () => {
        if (this.closed) return
        attempts += 1
        onState('reconnecting')
        const delay = Math.min(500 * 2 ** Math.min(attempts, 5), 10_000)
        this.reconnectTimer = window.setTimeout(open, delay)
      }
    }

    open()
    return () => this.disconnect()
  }

  disconnect(): void {
    this.closed = true
    if (this.reconnectTimer !== null) window.clearTimeout(this.reconnectTimer)
    this.reconnectTimer = null
    this.socket?.close()
    this.socket = null
  }
}
