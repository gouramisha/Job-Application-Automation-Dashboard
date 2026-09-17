import { Link } from 'react-router-dom'
import { Card, CardHeader, EmptyState } from '../ui'
import { OutcomeBadge, StatusBadge } from '../StatusBadge'
import { formatDate } from '../../lib/format'

export default function RecentApplications({ rows = [] }) {
  return (
    <Card>
      <CardHeader
        title="Recent applications"
        subtitle="Your latest submissions"
        action={
          <Link to="/applications" className="text-xs font-medium text-brand-600 hover:text-brand-700">
            View all
          </Link>
        }
      />
      {rows.length === 0 ? (
        <EmptyState
          icon="✈"
          title="No applications yet"
          description="Applications you record will show up here."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
                <th className="px-5 py-2.5 font-medium">Role</th>
                <th className="px-5 py-2.5 font-medium">Status</th>
                <th className="px-5 py-2.5 font-medium">Outcome</th>
                <th className="px-5 py-2.5 font-medium">Applied</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((row) => (
                <tr key={row.id} className="transition hover:bg-slate-50">
                  <td className="px-5 py-3">
                    <Link to={`/jobs/${row.job}`} className="font-medium text-slate-900 hover:text-brand-600">
                      {row.job_title}
                    </Link>
                    <p className="text-xs text-slate-500">{row.company_name}</p>
                  </td>
                  <td className="px-5 py-3"><StatusBadge status={row.job_status} /></td>
                  <td className="px-5 py-3"><OutcomeBadge outcome={row.outcome} label={row.outcome_display} /></td>
                  <td className="px-5 py-3 text-xs whitespace-nowrap text-slate-500">
                    {formatDate(row.submitted_at || row.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}
