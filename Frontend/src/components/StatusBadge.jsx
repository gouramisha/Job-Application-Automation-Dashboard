import { Badge } from './ui'
import { OUTCOME_CHIPS, RUN_STATUS_CHIPS, STATUS_BY_VALUE } from '../lib/constants'

export function StatusBadge({ status }) {
  const meta = STATUS_BY_VALUE[status]
  if (!meta) return <Badge className="bg-slate-100 text-slate-600 ring-slate-200">{status}</Badge>
  return <Badge className={meta.chip}>{meta.label}</Badge>
}

export function OutcomeBadge({ outcome, label }) {
  return (
    <Badge className={OUTCOME_CHIPS[outcome] || OUTCOME_CHIPS.draft}>{label || outcome}</Badge>
  )
}

export function RunStatusBadge({ status, label }) {
  return (
    <Badge className={RUN_STATUS_CHIPS[status] || RUN_STATUS_CHIPS.queued}>{label || status}</Badge>
  )
}

export function StatusSelect({ value, onChange, disabled, className = '' }) {
  const meta = STATUS_BY_VALUE[value]
  return (
    <select
      value={value}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value)}
      aria-label="Application status"
      className={`rounded-full border-0 py-1 pl-3 pr-8 text-xs font-medium ring-1 ring-inset transition
        disabled:cursor-not-allowed disabled:opacity-60 ${meta?.chip || ''} ${className}`}
    >
      {Object.values(STATUS_BY_VALUE).map((status) => (
        <option key={status.value} value={status.value}>
          {status.label}
        </option>
      ))}
    </select>
  )
}
