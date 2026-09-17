import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { jobs as jobsApi } from '../api/endpoints'
import { useApi } from '../hooks/useApi'
import { apiErrorMessage } from '../api/client'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, CardHeader, EmptyState, PageLoader } from '../components/ui'
import { StatusSelect } from '../components/StatusBadge'
import AutomationPanel from '../components/automation/AutomationPanel'
import StatusHistory from '../components/jobs/StatusHistory'
import QuickApplyModal from '../components/jobs/QuickApplyModal'
import { formatDate, splitCsv } from '../lib/format'

export default function JobDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [applyOpen, setApplyOpen] = useState(false)

  const { data: job, loading, error, reload } = useApi(() => jobsApi.get(id), [id])

  async function changeStatus(status) {
    try {
      await jobsApi.setStatus(id, { status })
      toast.success(`Moved to ${status}.`)
      reload()
    } catch (caught) {
      toast.error(apiErrorMessage(caught, 'Could not update the status.'))
    }
  }

  async function toggleFavourite() {
    try {
      await jobsApi.toggleFavourite(id)
      reload()
    } catch (caught) {
      toast.error(apiErrorMessage(caught))
    }
  }

  async function remove() {
    if (!window.confirm(`Delete "${job.job_title}"? This cannot be undone.`)) return
    try {
      await jobsApi.remove(id)
      toast.success('Job deleted.')
      navigate('/jobs')
    } catch (caught) {
      toast.error(apiErrorMessage(caught))
    }
  }

  if (loading && !job) return <PageLoader label="Loading job" />
  if (error) {
    return (
      <Card>
        <EmptyState icon="⚠" title="Could not load this job" description={error}
          action={<Link to="/jobs"><Button>Back to jobs</Button></Link>} />
      </Card>
    )
  }

  const skills = splitCsv(job.skills)

  return (
    <div className="space-y-5">
      <Link to="/jobs" className="inline-block text-sm text-slate-500 transition hover:text-slate-700">
        ← Back to jobs
      </Link>

      <Card className="px-5 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-semibold text-slate-900">{job.job_title}</h2>
              <button
                type="button"
                onClick={toggleFavourite}
                aria-label={job.is_favourite ? 'Remove from favourites' : 'Add to favourites'}
                className={`text-lg transition ${job.is_favourite ? 'text-amber-500' : 'text-slate-300 hover:text-amber-400'}`}
              >
                ★
              </button>
            </div>
            <p className="mt-0.5 text-slate-600">
              {job.company_name}
              {job.location && ` · ${job.location}`}
              {job.is_remote && <span className="ml-2 text-sm text-emerald-600">Remote</span>}
            </p>

            <dl className="mt-4 flex flex-wrap gap-x-8 gap-y-2 text-sm">
              <Detail label="Salary" value={job.salary} />
              <Detail label="Experience" value={job.experience_required} />
              <Detail label="Source" value={job.source_display} />
              <Detail label="Applied" value={formatDate(job.applied_date)} />
            </dl>
          </div>

          <div className="flex flex-col items-end gap-2">
            <StatusSelect value={job.status} onChange={changeStatus} />
            <div className="flex gap-2">
              <Button size="sm" onClick={() => setApplyOpen(true)}>Record application</Button>
              <Link to={`/jobs/${id}/edit`}><Button size="sm" variant="secondary">Edit</Button></Link>
            </div>
          </div>
        </div>

        {job.job_url && (
          <a
            href={job.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700"
          >
            Open the job posting ↗
          </a>
        )}

        {skills.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {skills.map((skill) => (
              <Badge key={skill} className="bg-slate-50 text-slate-700 ring-slate-200">{skill}</Badge>
            ))}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          {job.job_description && (
            <Card>
              <CardHeader title="Job description" />
              <p className="whitespace-pre-wrap px-5 py-4 text-sm leading-relaxed text-slate-700">
                {job.job_description}
              </p>
            </Card>
          )}

          {job.notes && (
            <Card>
              <CardHeader title="Your notes" />
              <p className="whitespace-pre-wrap px-5 py-4 text-sm leading-relaxed text-slate-700">{job.notes}</p>
            </Card>
          )}

          <AutomationPanel job={job} onRunFinished={reload} />
        </div>

        <div className="space-y-5">
          <StatusHistory entries={job.status_history} />
          <Card className="px-5 py-4">
            <h3 className="text-sm font-semibold text-slate-900">Danger zone</h3>
            <p className="mt-1 text-xs text-slate-500">
              Deleting removes the job, its applications and its reminders.
            </p>
            <Button variant="danger" size="sm" className="mt-3" onClick={remove}>Delete this job</Button>
          </Card>
        </div>
      </div>

      <QuickApplyModal
        open={applyOpen}
        job={job}
        onClose={() => setApplyOpen(false)}
        onDone={() => { setApplyOpen(false); reload() }}
      />
    </div>
  )
}

function Detail({ label, value }) {
  if (!value || value === '-') return null
  return (
    <div>
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="font-medium text-slate-700">{value}</dd>
    </div>
  )
}
