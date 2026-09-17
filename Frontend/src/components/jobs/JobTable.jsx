import { Link } from 'react-router-dom'
import { StatusSelect } from '../StatusBadge'
import { formatDate } from '../../lib/format'

export default function JobTable({ rows, onStatusChange, onDelete, busy }) {
  return (
    <div className={`card overflow-hidden transition ${busy ? 'opacity-60' : ''}`}>
      {/* Table on desktop, stacked cards on mobile - a six-column table is
          unreadable at phone width however it is scrolled. */}
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs text-slate-500">
              <th className="px-5 py-3 font-medium">Role</th>
              <th className="px-5 py-3 font-medium">Location</th>
              <th className="px-5 py-3 font-medium">Salary</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Applied</th>
              <th className="px-5 py-3 font-medium"><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((job) => (
              <tr key={job.id} className="transition hover:bg-slate-50">
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    {job.is_favourite && <span aria-label="Favourite" title="Favourite" className="text-amber-500">★</span>}
                    <Link to={`/jobs/${job.id}`} className="font-medium text-slate-900 hover:text-brand-600">
                      {job.job_title}
                    </Link>
                  </div>
                  <p className="text-xs text-slate-500">{job.company_name}</p>
                </td>
                <td className="px-5 py-3 text-slate-600">
                  {job.location || (job.is_remote ? 'Remote' : '-')}
                  {/* Only tag it when the location text does not already say so. */}
                  {job.is_remote && !/remote/i.test(job.location || '') && (
                    <span className="ml-1.5 text-xs text-emerald-600">Remote</span>
                  )}
                </td>
                <td className="px-5 py-3 text-slate-600">{job.salary || '-'}</td>
                <td className="px-5 py-3">
                  <StatusSelect value={job.status} onChange={(status) => onStatusChange(job, status)} disabled={busy} />
                </td>
                <td className="px-5 py-3 whitespace-nowrap text-xs text-slate-500">
                  {formatDate(job.applied_date)}
                </td>
                <td className="px-5 py-3 text-right whitespace-nowrap">
                  <Link to={`/jobs/${job.id}/edit`} className="text-xs font-medium text-slate-500 hover:text-brand-600">
                    Edit
                  </Link>
                  <button
                    type="button"
                    onClick={() => onDelete(job)}
                    className="ml-3 text-xs font-medium text-slate-400 transition hover:text-rose-600"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="divide-y divide-slate-100 md:hidden">
        {rows.map((job) => (
          <li key={job.id} className="px-4 py-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <Link to={`/jobs/${job.id}`} className="block truncate font-medium text-slate-900">
                  {job.job_title}
                </Link>
                <p className="truncate text-xs text-slate-500">{job.company_name}</p>
                <p className="mt-1 truncate text-xs text-slate-400">
                  {[job.location || (job.is_remote ? 'Remote' : ''), job.salary]
                    .filter(Boolean)
                    .join(' · ') || 'No location set'}
                </p>
              </div>
              <StatusSelect value={job.status} onChange={(status) => onStatusChange(job, status)} disabled={busy} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
