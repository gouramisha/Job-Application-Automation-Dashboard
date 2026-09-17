import { useState } from 'react'
import { analytics } from '../api/endpoints'
import { useApi } from '../hooks/useApi'
import { Button, Card, EmptyState, PageLoader } from '../components/ui'
import StatTile from '../components/StatTile'
import ApplicationsTrend from '../components/charts/ApplicationsTrend'
import ConversionFunnel from '../components/charts/ConversionFunnel'
import StatusMix from '../components/charts/StatusMix'
import CategoryBars from '../components/charts/CategoryBars'

const RANGES = [
  { days: 30, label: '30 days' },
  { days: 90, label: '90 days' },
  { days: 180, label: '6 months' },
  { days: 365, label: '1 year' },
]

export default function Analytics() {
  const [days, setDays] = useState(90)

  const { data: summary, loading: loadingSummary, error } = useApi(() => analytics.summary(), [])
  const { data: funnel } = useApi(() => analytics.funnel(), [])
  const { data: trend } = useApi(
    () => analytics.timeline({ days, bucket: days > 90 ? 'week' : 'day' }),
    [days],
  )
  const { data: breakdowns } = useApi(() => analytics.breakdowns(), [])

  if (loadingSummary && !summary) return <PageLoader label="Crunching your numbers" />
  if (error) {
    return (
      <Card>
        <EmptyState icon="⚠" title="Could not load analytics" description={error}
          action={<Button onClick={() => window.location.reload()}>Try again</Button>} />
      </Card>
    )
  }

  if (summary.total_jobs === 0) {
    return (
      <Card>
        <EmptyState
          icon="📊"
          title="No data to analyse yet"
          description="Analytics build themselves from the jobs you track and the applications you record. Add a few and come back."
        />
      </Card>
    )
  }

  const rangeControls = (
    <select
      className="input w-auto text-xs"
      value={days}
      onChange={(event) => setDays(Number(event.target.value))}
      aria-label="Time range"
    >
      {RANGES.map((range) => (
        <option key={range.days} value={range.days}>{range.label}</option>
      ))}
    </select>
  )

  return (
    <div className="space-y-6">
      <section aria-label="Headline rates" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          label="Applications sent"
          value={summary.applications_sent}
          sublabel={`out of ${summary.total_jobs} tracked`}
        />
        <StatTile
          label="Response rate"
          value={`${summary.response_rate}%`}
          sublabel="Any reply, positive or not"
        />
        <StatTile
          label="Interview rate"
          value={`${summary.interview_rate}%`}
          tone="warning"
          sublabel="Reached an interview"
        />
        <StatTile
          label="Offer rate"
          value={`${summary.success_rate}%`}
          tone="positive"
          sublabel="Ended in an offer"
        />
      </section>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ApplicationsTrend
            points={trend?.points ?? []}
            controls={rangeControls}
            title={`Applications sent (${trend?.bucket === 'week' ? 'per week' : 'per day'})`}
          />
        </div>
        <ConversionFunnel stages={funnel ?? []} />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <StatusMix rows={breakdowns?.by_status ?? []} title="Where your jobs stand" />
        <CategoryBars
          rows={breakdowns?.by_source ?? []}
          title="Where your jobs come from"
          subtitle="Which boards and referrals are feeding your pipeline"
          emptyLabel="Set a source on your jobs to see which channels work best."
        />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <CategoryBars
          rows={breakdowns?.top_companies ?? []}
          title="Most-tracked companies"
          subtitle="Where you have applied most often"
          emptyLabel="No companies tracked yet."
        />
        <CategoryBars
          rows={breakdowns?.by_method ?? []}
          title="How you applied"
          subtitle="Manual, automation-assisted, or official API"
          emptyLabel="Record an application to see the breakdown."
        />
      </div>
    </div>
  )
}
