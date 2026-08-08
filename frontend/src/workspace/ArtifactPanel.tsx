import { Braces, FileCode2, FileText, Table2 } from 'lucide-react'
import type { WorkspaceArtifact } from '../runtime/reducer'

const icons = { json: Braces, code: FileCode2, table: Table2, markdown: FileText, report: FileText }

export function ArtifactPanel({ artifacts }: { artifacts: WorkspaceArtifact[] }) {
  if (artifacts.length === 0) {
    return <p className="muru-panel-empty">Artifacts created by agents will be collected here.</p>
  }
  return (
    <div className="muru-artifact-list">
      {artifacts.map((artifact) => {
        const Icon = icons[artifact.kind as keyof typeof icons] ?? FileText
        return (
          <a key={artifact.id} href={`/api/v1/artifacts/${encodeURIComponent(artifact.id)}`} target="_blank" rel="noreferrer">
            <Icon size={16} aria-hidden="true" />
            <span><strong>{artifact.name}</strong><small>{artifact.kind} by {artifact.creator}</small></span>
          </a>
        )
      })}
    </div>
  )
}
