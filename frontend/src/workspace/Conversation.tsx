import { Bot, UserRound } from 'lucide-react'
import type { WorkspaceApproval, WorkspaceMessage } from '../runtime/reducer'
import { ApprovalCard } from './ApprovalCard'

interface ConversationProps {
  messages: WorkspaceMessage[]
  approvals: WorkspaceApproval[]
  onApproval: (id: string, decision: 'approve' | 'reject') => void
}

export function Conversation({ messages, approvals, onApproval }: ConversationProps) {
  if (messages.length === 0 && approvals.length === 0) {
    return (
      <div className="muru-conversation-empty">
        <Bot size={22} aria-hidden="true" />
        <strong>Ready for an objective</strong>
        <p>Messages, tool activity, approvals, and artifacts will appear as the runtime emits them.</p>
      </div>
    )
  }
  return (
    <div className="muru-conversation" aria-live="polite">
      {messages.filter((message) => message.role !== 'tool').map((message) => {
        const Icon = message.role === 'user' ? UserRound : Bot
        return (
          <article key={message.id} className={`muru-message is-${message.role}`}>
            <span className="muru-message-avatar"><Icon size={16} aria-hidden="true" /></span>
            <div>
              <header>{message.role === 'user' ? 'You' : 'AgentMuru'}{message.streaming && <span>Streaming</span>}</header>
              <p>{message.content}</p>
            </div>
          </article>
        )
      })}
      {approvals.map((approval) => (
        <ApprovalCard key={approval.id} approval={approval} onDecision={onApproval} />
      ))}
    </div>
  )
}
