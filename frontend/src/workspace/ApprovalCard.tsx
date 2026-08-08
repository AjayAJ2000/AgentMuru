import { OctagonAlert, ShieldCheck, X } from 'lucide-react'
import type { WorkspaceApproval } from '../runtime/reducer'

interface ApprovalCardProps {
  approval: WorkspaceApproval
  onDecision: (id: string, decision: 'approve' | 'reject') => void
}

export function ApprovalCard({ approval, onDecision }: ApprovalCardProps) {
  return (
    <article className={`muru-approval is-${approval.status}`} aria-label={`Approval for ${approval.toolName}`}>
      <header>
        <span className="muru-approval-icon"><OctagonAlert size={17} aria-hidden="true" /></span>
        <span><strong>Human approval required</strong><small>{approval.toolName}</small></span>
        <span className="muru-risk">{approval.risk} risk</span>
      </header>
      <dl>
        <div><dt>Permission</dt><dd>{approval.permission || 'No permission declared'}</dd></div>
        <div><dt>Arguments</dt><dd><pre>{JSON.stringify(approval.arguments, null, 2)}</pre></dd></div>
      </dl>
      {approval.status === 'pending' ? (
        <footer>
          <button className="muru-reject" type="button" onClick={() => onDecision(approval.id, 'reject')}>
            <X size={15} /> Reject
          </button>
          <button className="muru-approve" type="button" onClick={() => onDecision(approval.id, 'approve')}>
            <ShieldCheck size={15} /> Approve once
          </button>
        </footer>
      ) : <p className="muru-decision">Decision: {approval.status}</p>}
    </article>
  )
}
