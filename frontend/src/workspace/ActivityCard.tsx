import { Check, CircleAlert, LoaderCircle, Wrench } from 'lucide-react'
import type { ToolActivity } from '../runtime/reducer'

export function ActivityCard({ activity }: { activity: ToolActivity }) {
  const Icon = activity.status === 'completed'
    ? Check : activity.status === 'failed' ? CircleAlert : activity.status === 'running' ? LoaderCircle : Wrench
  return (
    <article className={`muru-activity is-${activity.status}`}>
      <div className="muru-activity-icon"><Icon size={15} aria-hidden="true" /></div>
      <div className="muru-activity-body">
        <div className="muru-activity-heading">
          <strong>{activity.name}</strong>
          <span>{activity.status}</span>
        </div>
        {Object.keys(activity.arguments).length > 0 && (
          <pre>{JSON.stringify(activity.arguments, null, 2)}</pre>
        )}
        {activity.errorCode && <p className="muru-inline-error">Error: {activity.errorCode}</p>}
      </div>
    </article>
  )
}
