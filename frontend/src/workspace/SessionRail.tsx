import { Plus, Radio } from 'lucide-react'
import type { SessionSummary } from '../runtime/protocol'

interface SessionRailProps {
  appName: string
  sessions: SessionSummary[]
  selectedId?: string
  onCreate: () => void
  onSelect: (id: string) => void
}

export function SessionRail({ appName, sessions, selectedId, onCreate, onSelect }: SessionRailProps) {
  return (
    <aside className="muru-session-rail" aria-label="Agent sessions">
      <header className="muru-brand">
        <span className="muru-brand-mark" aria-hidden="true">
          <img className="muru-brand-mark-image" src="/agentmuru-mark.png" alt="" width={512} height={512} />
        </span>
        <span><strong>{appName}</strong><small>Muru Workspace</small></span>
        <button className="muru-mobile-new" type="button" onClick={onCreate} aria-label="New session">
          <Plus size={17} />
        </button>
      </header>
      <button className="muru-primary-action" type="button" onClick={onCreate}>
        <Plus size={16} /> New session
      </button>
      <nav className="muru-session-list">
        <span className="muru-section-label">Sessions</span>
        {sessions.length === 0 ? (
          <p className="muru-rail-empty">No sessions yet. Start one when you are ready.</p>
        ) : sessions.map((session) => (
          <button
            key={session.id}
            className={`muru-session-item ${selectedId === session.id ? 'is-active' : ''}`}
            type="button"
            onClick={() => onSelect(session.id)}
          >
            <Radio size={14} aria-hidden="true" />
            <span>{session.title || 'Untitled session'}</span>
          </button>
        ))}
      </nav>
      <footer className="muru-rail-footer">
        Runtime events are authoritative. Workspace state can be replayed.
      </footer>
    </aside>
  )
}
