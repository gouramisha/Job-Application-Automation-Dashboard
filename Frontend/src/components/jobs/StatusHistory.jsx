import { Card, CardHeader } from '../ui'
import { STATUS_BY_VALUE } from '../../lib/constants'
import { formatDateTime } from '../../lib/format'

export default function StatusHistory({ entries = [] }) {
  return (
    <Card>
      <CardHeader title="Status history" subtitle="Every move this job has made" />
      {entries.length === 0 ? (
        <p className="px-5 py-4 text-sm text-slate-500">No changes recorded yet.</p>
      ) : (
        <ol className="px-5 py-4">
          {entries.map((entry, index) => {
            const to = STATUS_BY_VALUE[entry.to_status]
            const from = STATUS_BY_VALUE[entry.from_status]
            const isLast = index === entries.length - 1

            return (
              <li key={entry.id} className="relative flex gap-3 pb-4 last:pb-0">
                {/* The rail joins the dots but must stop at the final one. */}
                {!isLast && <span aria-hidden="true" className="absolute left-[5px] top-3 h-full w-px bg-slate-200" />}
                <span
                  aria-hidden="true"
                  className="relative mt-1 size-2.5 shrink-0 rounded-full ring-2 ring-white"
                  style={{ backgroundColor: to?.color || '#94a3b8' }}
                />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-slate-900">
                    {from ? (
                      <><span className="text-slate-500">{from.label}</span> → <span className="font-medium">{to?.label}</span></>
                    ) : (
                      <span className="font-medium">{to?.label || entry.to_status}</span>
                    )}
                  </p>
                  {entry.note && <p className="mt-0.5 text-xs text-slate-500">{entry.note}</p>}
                  <p className="mt-0.5 text-xs text-slate-400">{formatDateTime(entry.changed_at)}</p>
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </Card>
  )
}
