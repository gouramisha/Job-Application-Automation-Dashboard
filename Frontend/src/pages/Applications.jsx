import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { applications as applicationsApi } from '../api/endpoints'
import { useApi, useDebounced } from '../hooks/useApi'
import { apiErrorMessage } from '../api/client'
import { useToast } from '../context/ToastContext'
import { Button, Card, EmptyState, PageLoader } from '../components/ui'
import { OutcomeBadge, StatusBadge } from '../components/StatusBadge'
import { formatDate } from '../lib/format'

const OUTCOMES = [
  { value: '', label: 'All outcomes' },
  { value: 'prepared', label: 'Awaiting your submit' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'failed', label: 'Failed' },
  { value: 'draft', label: 'Draft' },
]

const METHODS = [
  { value: '', label: 'All methods' },
  { value: 'manual', label: 'Filled manually' },
  { value: 'assisted', label: 'Automation-assisted' },
  { value: 'api', label: 'Official API' },
]

export default function Applications() {
  const [search, setSearch] = useState('')
  const [outcome, setOutcome] = useState('')
  const [method, setMethod] = useState('')
  const [page, setPage] = useState(1)
  const toast = useToast()

  const debounced = useDebounced(search)
  const query = useMemo(
    () => ({ search: debounced, outcome, method, page }),
    [debounced, outcome, method, page],
  )

  const { data, loading, error, reload } = useApi(() => applicationsApi.list(query), [query])

  async function markSubmitted(row) {
    try {
      await applicationsApi.markSubmitted(row.id)
      toast.success('Marked as submitted.')
      reload()
    } catch (caught) {
      toast.error(apiErrorMessage(caught))
    }
  }

  const rows = data?.results ?? []
  const hasFilters = Boolean(debounced || outcome || method)

  return (
    <div className="space-y-5">
      <div className="card flex flex-wrap items-center gap-3 px-4 py-3">
        <input
          type="search"
          className="input min-w-[180px] flex-1"
          placeholder="Search company or role…"
          value={search}
          onChange={(event) => { setSearch(event.target.value); setPage(1) }}
          aria-label="Search applications"
        />
        <select className="input w-auto" value={outcome} onChange={(event) => { setOutcome(event.target.value); setPage(1) }} aria-label="Filter by outcome">
          {OUTCOMES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
        <select className="input w-auto" value={method} onChange={(event) => { setMethod(event.target.value); setPage(1) }} aria-label="Filter by method">
          {METHODS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
        {data && <span className="text-xs text-slate-500">{data.count} total</span>}
      </div>

      {error ? (
        <Card><EmptyState icon="⚠" title="Could not load applications" description={error}
          action={<Button onClick={reload}>Try again</Button>} /></Card>
      ) : loading && !data ? (
        <PageLoader label="Loading applications" />
      ) : rows.length === 0 ? (
        <Card>
          <EmptyState
            icon="✈"
            title={hasFilters ? 'Nothing matches those filters' : 'No applications yet'}
            description={
              hasFilters
                ? 'Try clearing a filter to widen the search.'
                : 'Record an application from a job page, or let assisted filling create one for you.'
            }
            action={!hasFilters && <Link to="/jobs"><Button>Go to your jobs</Button></Link>}
          />
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs text-slate-500">
                  <th className="px-5 py-3 font-medium">Role</th>
                  <th className="px-5 py-3 font-medium">Resume</th>
                  <th className="px-5 py-3 font-medium">Method</th>
                  <th className="px-5 py-3 font-medium">Outcome</th>
                  <th className="px-5 py-3 font-medium">Job status</th>
                  <th className="px-5 py-3 font-medium">Date</th>
                  <th className="px-5 py-3"><span className="sr-only">Actions</span></th>
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
                    <td className="px-5 py-3 text-xs text-slate-600">{row.resume_label || '-'}</td>
                    <td className="px-5 py-3 text-xs text-slate-600">{row.method_display}</td>
                    <td className="px-5 py-3"><OutcomeBadge outcome={row.outcome} label={row.outcome_display} /></td>
                    <td className="px-5 py-3"><StatusBadge status={row.job_status} /></td>
                    <td className="px-5 py-3 text-xs whitespace-nowrap text-slate-500">
                      {formatDate(row.submitted_at || row.created_at)}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {row.outcome === 'prepared' && (
                        <Button size="sm" variant="secondary" onClick={() => markSubmitted(row)}>
                          Mark submitted
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {data && data.count > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-500">Page {page} of {Math.ceil(data.count / 20)}</p>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>Previous</Button>
            <Button variant="secondary" size="sm" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>Next</Button>
          </div>
        </div>
      )}
    </div>
  )
}
