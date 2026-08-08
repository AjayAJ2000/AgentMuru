import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { initialWorkspaceState } from '../runtime/reducer'
import { ApprovalCard } from './ApprovalCard'
import { Workspace } from './Workspace'

describe('Muru Workspace', () => {
  it('renders an intentional empty state before a session is selected', () => {
    const html = renderToStaticMarkup(
      <Workspace
        appName="AgentMuru"
        sessions={[]}
        state={null}
        connection="connected"
        onCreateSession={() => undefined}
        onSelectSession={() => undefined}
        onSubmit={() => undefined}
        onCancel={() => undefined}
        onApproval={() => undefined}
      />,
    )

    expect(html).toContain('Start an agent session')
    expect(html).toContain('New session')
  })

  it('renders approval controls with explicit risk and permission context', () => {
    const html = renderToStaticMarkup(
      <ApprovalCard
        approval={{
          id: 'approval-1',
          runId: 'run-1',
          toolCallId: 'call-1',
          toolName: 'drop_table',
          arguments: { name: 'customers' },
          permission: 'database.write',
          risk: 'high',
          status: 'pending',
        }}
        onDecision={() => undefined}
      />,
    )

    expect(html).toContain('database.write')
    expect(html).toContain('Approve once')
    expect(html).toContain('Reject')
  })

  it('renders connection and active run state accessibly', () => {
    const state = initialWorkspaceState('session-1')
    state.runs['run-1'] = { id: 'run-1', agent: 'researcher', status: 'running' }
    const html = renderToStaticMarkup(
      <Workspace
        appName="AgentMuru"
        sessions={[{ id: 'session-1', title: 'Research', updatedAt: '', eventSequence: 0 }]}
        state={state}
        connection="reconnecting"
        onCreateSession={() => undefined}
        onSelectSession={() => undefined}
        onSubmit={() => undefined}
        onCancel={() => undefined}
        onApproval={() => undefined}
      />,
    )

    expect(html).toContain('Reconnecting')
    expect(html).toContain('Cancel run')
  })
})
