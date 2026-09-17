import { Link } from 'react-router-dom'
import { jobs as jobsApi } from '../../api/endpoints'
import { useApi } from '../../hooks/useApi'
import { Badge, Button, Card, EmptyState, PageLoader } from '../ui'

/** Saved jobs ranked against the preferences on the user's profile.
 *  Every row explains its own score - a number with no reason is not advice. */
export default function JobMatches() {
  const { data, loading, error } = useApi(() => jobsApi.matches({ min_score: 1 }), [])

  if (loading) return <PageLoader label="Scoring your saved jobs" />
  if (error) {
    return <Card><EmptyState icon="⚠" title="Could not load matches" description={error} /></Card>
  }

  const rows = data?.results ?? []

  if (rows.length === 0) {
    return (
      <Card>
        <EmptyState
          icon="🎯"
          title="No matches to show yet"
          description="Matching compares your saved jobs against the roles, locations, experience and skills on your profile. Fill those in, then save a few jobs."
          action={<Link to="/profile"><Button>Complete your profile</Button></Link>}
        />
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">
        {rows.length} saved {rows.length === 1 ? 'job' : 'jobs'} scored against your profile preferences.
      </p>

      {rows.map((job) => (
        <Card key={job.id} className="px-5 py-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <Link to={`/jobs/${job.id}`} className="font-medium text-slate-900 hover:text-brand-600">
                {job.job_title}
              </Link>
              <p className="text-sm text-slate-500">
                {job.company_name}
                {job.location && ` · ${job.location}`}
              </p>

              <ul className="mt-2.5 flex flex-wrap gap-1.5">
                {job.match_reasons.map((reason) => (
                  <li key={reason}>
                    <Badge className="bg-slate-50 text-slate-600 ring-slate-200">{reason}</Badge>
                  </li>
                ))}
              </ul>
            </div>

            <div className="shrink-0 text-right">
              <MatchScore score={job.match_score} />
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}

function MatchScore({ score }) {
  // Three bands, each with its own label, so the number is never the only cue.
  const band =
    score >= 70 ? { label: 'Strong match', tone: 'text-emerald-700', bar: 'bg-emerald-500' }
    : score >= 40 ? { label: 'Partial match', tone: 'text-amber-700', bar: 'bg-amber-500' }
    : { label: 'Weak match', tone: 'text-slate-600', bar: 'bg-slate-400' }

  return (
    <div className="w-28">
      <p className={`tabular text-lg font-semibold ${band.tone}`}>{score}%</p>
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${band.bar}`} style={{ width: `${score}%` }} />
      </div>
      <p className="mt-1 text-xs text-slate-500">{band.label}</p>
    </div>
  )
}
