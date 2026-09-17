import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { jobs as jobsApi } from '../api/endpoints'
import { useApi, useDebounced } from '../hooks/useApi'
import { apiErrorMessage } from '../api/client'
import { useToast } from '../context/ToastContext'
import { Button, Card, EmptyState, PageLoader } from '../components/ui'
import JobFilters from '../components/jobs/JobFilters'
import JobTable from '../components/jobs/JobTable'
import JobMatches from '../components/jobs/JobMatches'

const TABS = [
  { key: 'all', label: 'All jobs' },
  { key: 'matches', label: 'Matches for you' },
]

export default function Jobs() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [tab, setTab] = useState('all')
  const [page, setPage] = useState(1)
  const toast = useToast()

  const [filters, setFilters] = useState(() => ({
    search: searchParams.get('search') || '',
    status: searchParams.get('status') || '',
    source: searchParams.get('source') || '',
    ordering: searchParams.get('ordering') || '-created_at',
  }))

  const debouncedSearch = useDebounced(filters.search)

  // Keep the URL in step with the filters so a filtered view is shareable and
  // survives a refresh.
  useEffect(() => {
    const next = {}
    if (debouncedSearch) next.search = debouncedSearch
    if (filters.status) next.status = filters.status
    if (filters.source) next.source = filters.source
    if (filters.ordering !== '-created_at') next.ordering = filters.ordering
    setSearchParams(next, { replace: true })
    setPage(1)
  }, [debouncedSearch, filters.status, filters.source, filters.ordering, setSearchParams])

  const query = useMemo(
    () => ({
      search: debouncedSearch,
      status: filters.status,
      source: filters.source,
      ordering: filters.ordering,
      page,
    }),
    [debouncedSearch, filters.status, filters.source, filters.ordering, page],
  )

  const { data, loading, error, reload } = useApi(() => jobsApi.list(query), [query])
  const { data: options } = useApi(() => jobsApi.options(), [])

  const updateStatus = useCallback(
    async (job, status) => {
      try {
        await jobsApi.setStatus(job.id, { status })
        toast.success(`${job.job_title} moved to ${status}.`)
        reload()
      } catch (caught) {
        toast.error(apiErrorMessage(caught, 'Could not update that job.'))
      }
    },
    [reload, toast],
  )

  const remove = useCallback(
    async (job) => {
      if (!window.confirm(`Delete "${job.job_title}" at ${job.company_name}? This cannot be undone.`)) return
      try {
        await jobsApi.remove(job.id)
        toast.success('Job deleted.')
        reload()
      } catch (caught) {
        toast.error(apiErrorMessage(caught, 'Could not delete that job.'))
      }
    },
    [reload, toast],
  )

  const hasFilters = Boolean(debouncedSearch || filters.status || filters.source)
  const results = data?.results ?? []
  const totalPages = data ? Math.ceil(data.count / 20) : 1

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-lg bg-slate-100 p-0.5">
          {TABS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setTab(item.key)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                tab === item.key ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
        {/* The topbar carries "+ Add job" at every width above mobile, so the
            button here only appears where that one is hidden. */}
        <Link to="/jobs/new" className="sm:hidden">
          <Button size="sm">+ Add job</Button>
        </Link>
      </div>

      {tab === 'matches' ? (
        <JobMatches />
      ) : (
        <>
          <JobFilters
            filters={filters}
            onChange={setFilters}
            options={options}
            resultCount={data?.count}
            loading={loading}
          />

          {error ? (
            <Card>
              <EmptyState icon="⚠" title="Could not load your jobs" description={error}
                action={<Button onClick={reload}>Try again</Button>} />
            </Card>
          ) : loading && !data ? (
            <PageLoader label="Loading jobs" />
          ) : results.length === 0 ? (
            <Card>
              <EmptyState
                icon={hasFilters ? '🔍' : '💼'}
                title={hasFilters ? 'No jobs match those filters' : 'No jobs yet'}
                description={
                  hasFilters
                    ? 'Try a different search term, or clear the filters to see everything.'
                    : 'Add the roles you are interested in and track them from Saved through to Selected.'
                }
                action={
                  hasFilters ? (
                    <Button variant="secondary" onClick={() => setFilters({ search: '', status: '', source: '', ordering: '-created_at' })}>
                      Clear filters
                    </Button>
                  ) : (
                    <Link to="/jobs/new"><Button>Add your first job</Button></Link>
                  )
                }
              />
            </Card>
          ) : (
            <>
              <JobTable rows={results} onStatusChange={updateStatus} onDelete={remove} busy={loading} />

              {totalPages > 1 && (
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-500">
                    Page {page} of {totalPages} · {data.count} jobs
                  </p>
                  <div className="flex gap-2">
                    <Button variant="secondary" size="sm" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>
                      Previous
                    </Button>
                    <Button variant="secondary" size="sm" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
