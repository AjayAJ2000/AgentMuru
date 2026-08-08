import { useCallback, useEffect, useRef, useState } from 'react'
import { RuntimeClient, type AppMetadata } from './runtime/client'
import type { ConnectionState, RuntimeEvent, SessionSummary } from './runtime/protocol'
import { hydrateWorkspace, reduceWorkspace, type WorkspaceState } from './runtime/reducer'
import { Workspace } from './workspace/Workspace'

export default function App() {
  const clientRef = useRef<RuntimeClient | null>(null)
  if (clientRef.current === null) clientRef.current = new RuntimeClient()
  const client = clientRef.current
  const [metadata, setMetadata] = useState<AppMetadata | null>(null)
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [workspace, setWorkspace] = useState<WorkspaceState | null>(null)
  const [connection, setConnection] = useState<ConnectionState>('offline')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    Promise.all([client.app(), client.sessions()])
      .then(([app, availableSessions]) => {
        if (!active) return
        setMetadata(app)
        setSessions(availableSessions)
        if (availableSessions[0]) setSelectedId(availableSessions[0].id)
      })
      .catch((reason: unknown) => {
        if (!active) return
        setConnection('error')
        setError(reason instanceof Error ? reason.message : 'Unable to load AgentMuru')
      })
    return () => {
      active = false
      client.disconnect()
    }
  }, [client])

  useEffect(() => {
    if (!selectedId) {
      setWorkspace(null)
      setConnection('offline')
      return
    }
    let active = true
    let disconnect: () => void = () => undefined
    setConnection('connecting')
    setError(null)
    client.session(selectedId)
      .then((snapshot) => {
        if (!active) return
        const hydrated = hydrateWorkspace(snapshot)
        setWorkspace(hydrated)
        disconnect = client.connect(
          selectedId,
          hydrated.lastSequence,
          (event: RuntimeEvent) => {
            setWorkspace((current) => current ? reduceWorkspace(current, event) : current)
            setSessions((current) => current.map((session) => session.id === event.session_id
              ? { ...session, eventSequence: event.sequence }
              : session))
          },
          setConnection,
          setError,
        )
      })
      .catch((reason: unknown) => {
        if (!active) return
        setConnection('error')
        setError(reason instanceof Error ? reason.message : 'Unable to load session')
      })
    return () => {
      active = false
      disconnect()
    }
  }, [client, selectedId])

  const createSession = useCallback(() => {
    setError(null)
    client.createSession(`Session ${sessions.length + 1}`)
      .then((session) => {
        const summary: SessionSummary = {
          id: session.id,
          title: session.title,
          updatedAt: session.updated_at,
          eventSequence: session.event_sequence,
        }
        setSessions((current) => [summary, ...current])
        setSelectedId(session.id)
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Unable to create session'))
  }, [client, sessions.length])

  const submit = useCallback((content: string) => {
    if (!selectedId) return
    client.submit(selectedId, content)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Unable to start run'))
  }, [client, selectedId])

  const cancel = useCallback((runId: string) => {
    client.cancel(runId)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Unable to cancel run'))
  }, [client])

  const decide = useCallback((approvalId: string, decision: 'approve' | 'reject') => {
    client.decide(approvalId, decision)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Unable to record approval'))
  }, [client])

  return (
    <Workspace
      appName={metadata?.title || 'AgentMuru'}
      sessions={sessions}
      state={workspace}
      connection={connection}
      error={error}
      onCreateSession={createSession}
      onSelectSession={setSelectedId}
      onSubmit={submit}
      onCancel={cancel}
      onApproval={decide}
    />
  )
}
