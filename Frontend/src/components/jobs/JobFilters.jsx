import { Spinner } from '../ui'
import { JOB_STATUSES } from '../../lib/constants'

const SORTS = [
  { value: '-created_at', label: 'Newest first' },
  { value: 'created_at', label: 'Oldest first' },
  { value: '-applied_date', label: 'Recently applied' },
  { value: 'company_name', label: 'Company A-Z' },
  { value: 'job_title', label: 'Job title A-Z' },
]

export default function JobFilters({ filters, onChange, options, resultCount, loading }) {
  const set = (field) => (event) => onChange({ ...filters, [field]: event.target.value })
  const active = Boolean(filters.search || filters.status || filters.source)

  return (
    <div className="card px-4 py-3">
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[200px] flex-1">
          <span aria-hidden="true" className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
            ⌕
          </span>
          <input
            type="search"
            className="input pl-8"
            placeholder="Search company, title, skills, notes…"
            value={filters.search}
            onChange={set('search')}
            aria-label="Search jobs"
          />
        </div>

        <select className="input w-auto" value={filters.status} onChange={set('status')} aria-label="Filter by status">
          <option value="">All statuses</option>
          {JOB_STATUSES.map((status) => (
            <option key={status.value} value={status.value}>{status.label}</option>
          ))}
        </select>

        <select className="input w-auto" value={filters.source} onChange={set('source')} aria-label="Filter by source">
          <option value="">All sources</option>
          {(options?.sources ?? []).map((source) => (
            <option key={source.value} value={source.value}>{source.label}</option>
          ))}
        </select>

        <select className="input w-auto" value={filters.ordering} onChange={set('ordering')} aria-label="Sort jobs">
          {SORTS.map((sort) => (
            <option key={sort.value} value={sort.value}>{sort.label}</option>
          ))}
        </select>

        {active && (
          <button
            type="button"
            onClick={() => onChange({ ...filters, search: '', status: '', source: '' })}
            className="text-sm font-medium text-slate-500 transition hover:text-slate-700"
          >
            Clear
          </button>
        )}
      </div>

      <div className="mt-2 flex h-4 items-center gap-2 text-xs text-slate-500">
        {loading ? (
          <><Spinner className="size-3" /> Searching…</>
        ) : resultCount !== undefined ? (
          <span>{resultCount} {resultCount === 1 ? 'job' : 'jobs'}</span>
        ) : null}
      </div>
    </div>
  )
}
