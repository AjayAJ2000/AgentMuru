import { Send, Square } from 'lucide-react'
import { FormEvent, useState } from 'react'

interface RunComposerProps {
  disabled: boolean
  running: boolean
  onSubmit: (content: string) => void
  onCancel: () => void
}

export function RunComposer({ disabled, running, onSubmit, onCancel }: RunComposerProps) {
  const [content, setContent] = useState('')
  const submit = (event: FormEvent) => {
    event.preventDefault()
    const value = content.trim()
    if (!value || disabled) return
    onSubmit(value)
    setContent('')
  }
  return (
    <form className="muru-composer" onSubmit={submit}>
      <label htmlFor="muru-objective">Give the agent an objective</label>
      <div>
        <textarea
          id="muru-objective"
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder="Investigate the failed pipeline and prepare a remediation plan"
          rows={2}
          disabled={disabled}
        />
        {running ? (
          <button className="muru-cancel" type="button" onClick={onCancel}><Square size={15} /> Cancel run</button>
        ) : (
          <button className="muru-send" type="submit" disabled={disabled || !content.trim()}><Send size={15} /> Run</button>
        )}
      </div>
      <small>Tool calls are visible. Risky actions pause for approval.</small>
    </form>
  )
}
