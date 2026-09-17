import { useState } from 'react'
import { Link } from 'react-router-dom'
import { analytics } from '../api/endpoints'
import { useApi } from '../hooks/useApi'
import { Button, Card, EmptyState, PageLoader } from '../components/ui'
import StatTile from '../components/StatTile'
import ApplicationsTrend from '../components/charts/ApplicationsTrend'
import ConversionFunnel from '../components/charts/ConversionFunnel'
import RecentApplications from '../components/dashboard/RecentApplications'
import UpcomingFollowUps from '../components/dashboard/UpcomingFollowUps'
import { useAuth } from '../context/AuthContext'

const RANGES = [
  { days: 14, label: '14d' },
  { days: 30, label: '30d' },
  { days: 90, label: '90d' },
]

export default function Dashboard() {
  const [days, setDays] = useState(30)
  const { user } = useAuth()
  const { data, loading, error } = useApi(() => analytics.dashboard({ days }), [days])

  if (loading && !data) return <PageLoader label="Building your dashboard" />

  if (error) {
    return (
      <Card>
        <EmptyState
          icon="⚠"
          title="Could not load your dashboard"
          description={error}
          action={<Button onClick={() => window.location.reload()}>Try again</Button>}
        />
      </Card>
    )
  }

  const { summary, funnel, timeline, recent_applications: recent, upcoming_reminders: reminders } = data
  const firstName = user?.first_name || 'there'
  const hasNothing = summary.total_jobs === 0

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Welcome back, {firstName}</h2>
        <p className="mt-0.5 text-sm text-slate-500">
          {hasNothing
            ? 'Add your first job to start tracking your search.'
            : `You are tracking ${summary.total_jobs} ${summary.total_jobs === 1 ? 'job' : 'jobs'}, with ${summary.in_progress} still live.`}
        </p>
      </div>

      {hasNothing ? (
        <Card>
          <EmptyState
            icon="💼"
            title="Your dashboard is ready and empty"
            description="Add a job you are interested in, or one you have already applied to. Reminders, analytics and the funnel all build themselves from there."
            action={
              <Link to="/jobs/new">
                <Button size="lg">Add your first job</Button>
              </Link>
            }
          />
        </Card>
      ) : (
        <>
          <section aria-label="Key figures" className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <StatTile label="Total jobs" value={summary.total_jobs} to="/jobs" />
            <StatTile label="Applications sent" value={summary.applications_sent} tone="brand" to="/applications" />
            <StatTile label="Shortlisted" value={summary.shortlisted} to="/jobs?status=shortlisted" />
            <StatTile label="Interviews" value={summary.interviews} tone="warning" to="/jobs?status=interview" />
            <StatTile label="Selected" value={summary.selected} tone="positive" to="/jobs?status=selected" />
            <StatTile label="Rejected" value={summary.rejected} tone="negative" to="/jobs?status=rejected" />
          </section>

          <section aria-label="Conversion rates" className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <StatTile
              label="Response rate"
              value={`${summary.response_rate}%`}
              sublabel={`Heard back on ${summary.applications_sent} sent`}
            />
            <StatTile
              label="Interview rate"
              value={`${summary.interview_rate}%`}
              tone="warning"
              sublabel="Reached an interview stage"
            />
            <StatTile
              label="Success rate"
              value={`${summary.success_rate}%`}
              tone="positive"
              sublabel="Ended in an offer"
            />
          </section>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ApplicationsTrend
                points={timeline}
                controls={
                  <div className="flex rounded-lg bg-slate-100 p-0.5">
                    {RANGES.map((range) => (
                      <button
                        key={range.days}
                        type="button"
                        onClick={() => setDays(range.days)}
                        className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                          days === range.days
                            ? 'bg-white text-slate-900 shadow-sm'
                            : 'text-slate-500 hover:text-slate-700'
                        }`}
                      >
                        {range.label}
                      </button>
                    ))}
                  </div>
                }
              />
            </div>
            <ConversionFunnel stages={funnel} />
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <RecentApplications rows={recent} />
            </div>
            <UpcomingFollowUps rows={reminders} overdue={summary.overdue_reminders} />
          </div>
        </>
      )}
    </div>
  )
}
