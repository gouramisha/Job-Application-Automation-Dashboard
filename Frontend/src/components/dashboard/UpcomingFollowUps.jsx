import { Link } from 'react-router-dom'
import { Card, CardHeader, EmptyState } from '../ui'
import { relativeDate } from '../../lib/format'

export default function UpcomingFollowUps({ rows = [], overdue = 0 }) {
  return (
    <Card>
      <CardHeader
        title="Upcoming follow-ups"
        subtitle={overdue > 0 ? `${overdue} overdue` : 'Next two weeks'}
        action={
          <Link to="/reminders" className="text-xs font-medium text-brand-600 hover:text-brand-700">
            View all
          </Link>
        }
      />
      {rows.length === 0 ? (
        <EmptyState
          icon="✓"
          title="Nothing due"
          description="Follow-ups are scheduled automatically when you record an application."
        />
      ) : (
        <ul className="divide-y divide-slate-100">
          {rows.map((row) => (
            <li key={row.id} className="px-5 py-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  {row.job ? (
                    <Link to={`/jobs/${row.job}`} className="block truncate text-sm font-medium text-slate-900 hover:text-brand-600">
                      {row.title}
                    </Link>
                  ) : (
                    <p className="truncate text-sm font-medium text-slate-900">{row.title}</p>
                  )}
                  <p className="mt-0.5 text-xs text-slate-500">{row.kind_display}</p>
                </div>
                <span
                  className={`shrink-0 text-xs font-medium ${
                    row.is_overdue ? 'text-rose-600' : 'text-slate-500'
                  }`}
                >
                  {relativeDate(row.due_date)}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
