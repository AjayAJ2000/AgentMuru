import { Activity, Archive, CircleAlert, PlugZap, RotateCw } from 'lucide-react'
import { useState } from 'react'
import type { ConnectionState, SessionSummary } from '../runtime/protocol'
import type { WorkspaceState } from '../runtime/reducer'
import { ActivityCard } from './ActivityCard'
import { ArtifactPanel } from './ArtifactPanel'
import { Conversation } from './Conversation'
import { RunComposer } from './RunComposer'
import { SessionRail } from './SessionRail'
import { TracePanel } from './TracePanel'

interface WorkspaceProps {
  appName: string
  sessions: SessionSummary[]
  state: WorkspaceState | null
  connection: ConnectionState
  error?: string | null
  onCreateSession: () => void
  onSelectSession: (id: string) => void
  onSubmit: (content: string) => void
  onCancel: (runId: string) => void
  onApproval: (id: string, decision: 'approve' | 'reject') => void
}

export function Workspace(props: WorkspaceProps) {
  const [panel, setPanel] = useState<'artifacts' | 'trace'>('artifacts')
  const activeRun = props.state
    ? Object.values(props.state.runs).find((run) => ['queued', 'running', 'waiting_approval'].includes(run.status))
    : undefined
  const connectionLabel = props.connection === 'connected'
    ? 'Runtime connected' : props.connection === 'reconnecting' ? 'Reconnecting' : props.connection

  return (
    <main className="muru-workspace">
      <SessionRail
        appName={props.appName}
        sessions={props.sessions}
        selectedId={props.state?.sessionId}
        onCreate={props.onCreateSession}
        onSelect={props.onSelectSession}
      />
      {!props.state ? (
        <section className="muru-empty-workspace">
          <div className="muru-empty-mark"><PlugZap size={24} /></div>
          <h1>Start an agent session</h1>
          <p>Run an objective with streaming, governed tools, artifacts, and a replayable trace.</p>
          <button className="muru-primary-action" type="button" onClick={props.onCreateSession}>New session</button>
        </section>
      ) : (
        <>
          <section className="muru-run-column">
            <header className="muru-run-header">
              <div>
                <span className={`muru-connection is-${props.connection}`}>
                  {props.connection === 'reconnecting' && <RotateCw size={12} />}{connectionLabel}
                </span>
                <h1>{props.state.title || 'Untitled session'}</h1>
              </div>
              <div className="muru-run-state">
                <small>Active run</small>
                <strong>{activeRun ? `${activeRun.agent} · ${activeRun.status.replace('_', ' ')}` : 'Idle'}</strong>
              </div>
            </header>
            {(props.error || props.state.protocolError) && (
              <div className="muru-error-banner" role="alert"><CircleAlert size={16} />{props.error || props.state.protocolError}</div>
            )}
            <div className="muru-run-scroll">
              <Conversation
                messages={props.state.messages}
                approvals={props.state.approvals}
                onApproval={props.onApproval}
              />
              {props.state.activities.length > 0 && (
                <section className="muru-activity-section" aria-label="Tool activity">
                  <h2>Runtime activity</h2>
                  {props.state.activities.map((activity) => <ActivityCard key={activity.id} activity={activity} />)}
                </section>
              )}
            </div>
            <RunComposer
              disabled={props.connection !== 'connected'}
              running={Boolean(activeRun)}
              onSubmit={props.onSubmit}
              onCancel={() => activeRun && props.onCancel(activeRun.id)}
            />
          </section>
          <aside className="muru-context-panel">
            <div className="muru-panel-tabs" role="tablist" aria-label="Run context">
              <button type="button" role="tab" aria-selected={panel === 'artifacts'} onClick={() => setPanel('artifacts')}>
                <Archive size={14} /> Artifacts <span>{props.state.artifacts.length}</span>
              </button>
              <button type="button" role="tab" aria-selected={panel === 'trace'} onClick={() => setPanel('trace')}>
                <Activity size={14} /> Trace
              </button>
            </div>
            <div className="muru-panel-content">
              {panel === 'artifacts'
                ? <ArtifactPanel artifacts={props.state.artifacts} />
                : <TracePanel spans={props.state.spans} usage={props.state.usage} />}
            </div>
          </aside>
        </>
      )}
    </main>
  )
}
