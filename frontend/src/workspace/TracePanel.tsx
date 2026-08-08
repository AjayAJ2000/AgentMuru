import { Activity, CornerDownRight } from 'lucide-react'
import type { TraceSpan, WorkspaceUsage } from '../runtime/reducer'

export function TracePanel({ spans, usage }: { spans: TraceSpan[]; usage: WorkspaceUsage }) {
  return (
    <div className="muru-trace-panel">
      <div className="muru-usage-grid">
        <span><small>Input</small><strong>{usage.inputTokens}</strong></span>
        <span><small>Output</small><strong>{usage.outputTokens}</strong></span>
        <span><small>Total</small><strong>{usage.totalTokens}</strong></span>
        <span><small>Cost</small><strong>{usage.cost ? `$${usage.cost.toFixed(4)}` : 'n/a'}</strong></span>
      </div>
      {spans.length === 0 ? (
        <p className="muru-panel-empty">Trace spans become available as model and tool work executes.</p>
      ) : (
        <ol className="muru-span-list">
          {spans.map((span) => (
            <li key={span.id}>
              {span.parentId ? <CornerDownRight size={14} /> : <Activity size={14} />}
              <span><strong>{span.name}</strong><small>{span.kind} · {span.status}</small></span>
              {span.durationMs !== undefined && <time>{span.durationMs.toFixed(0)} ms</time>}
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
