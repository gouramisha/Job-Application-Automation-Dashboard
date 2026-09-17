export const JOB_STATUSES = [
  { value: 'saved', label: 'Saved', color: 'var(--color-status-saved)', chip: 'bg-slate-100 text-slate-700 ring-slate-200' },
  { value: 'applied', label: 'Applied', color: 'var(--color-status-applied)', chip: 'bg-indigo-50 text-indigo-700 ring-indigo-200' },
  { value: 'shortlisted', label: 'Shortlisted', color: 'var(--color-status-shortlisted)', chip: 'bg-cyan-50 text-cyan-700 ring-cyan-200' },
  { value: 'interview', label: 'Interview', color: 'var(--color-status-interview)', chip: 'bg-amber-50 text-amber-700 ring-amber-200' },
  { value: 'selected', label: 'Selected', color: 'var(--color-status-selected)', chip: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
  { value: 'rejected', label: 'Rejected', color: 'var(--color-status-rejected)', chip: 'bg-rose-50 text-rose-700 ring-rose-200' },
]

export const STATUS_BY_VALUE = Object.fromEntries(JOB_STATUSES.map((s) => [s.value, s]))

export const OUTCOME_CHIPS = {
  draft: 'bg-slate-100 text-slate-700 ring-slate-200',
  prepared: 'bg-amber-50 text-amber-700 ring-amber-200',
  submitted: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  failed: 'bg-rose-50 text-rose-700 ring-rose-200',
  abandoned: 'bg-slate-100 text-slate-500 ring-slate-200',
}

export const RUN_STATUS_CHIPS = {
  queued: 'bg-slate-100 text-slate-700 ring-slate-200',
  running: 'bg-blue-50 text-blue-700 ring-blue-200',
  awaiting_review: 'bg-amber-50 text-amber-700 ring-amber-200',
  submitted: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  failed: 'bg-rose-50 text-rose-700 ring-rose-200',
  cancelled: 'bg-slate-100 text-slate-500 ring-slate-200',
  unsupported: 'bg-orange-50 text-orange-700 ring-orange-200',
}

export const REMINDER_KINDS = [
  { value: 'follow_up', label: 'Follow up' },
  { value: 'interview', label: 'Interview' },
  { value: 'deadline', label: 'Application deadline' },
  { value: 'task', label: 'Task' },
]

/* ---------------------------------------------------------------------------
 * Chart colour.
 *
 * Badges above and charts below use different palettes on purpose. A badge
 * always carries its label text, so colour there is reinforcement. A chart
 * mark often does not, so it follows the stricter rules:
 *
 *  - The six statuses are ORDINAL (Saved -> Applied -> ... -> Selected is a
 *    sequence, not a set of names), so charts render them as a single-hue
 *    ramp, light to dark. Rejected leaves that sequence, so it takes the
 *    reserved critical red instead of a ramp step.
 *  - A chart of one series - applications per day, jobs per source - uses ONE
 *    colour for every mark. Colouring those bars individually would encode
 *    bar length twice and say nothing new.
 *  - The categorical list is only for genuinely nominal, multi-series charts.
 *
 * Every ramp below was checked with the palette validator for lightness
 * monotonicity, step separation, colour-vision separation and contrast against
 * the chart surface. Re-run it before changing any value here.
 * ------------------------------------------------------------------------ */

/** Single-series marks: bars, areas, lines. */
export const CHART_PRIMARY = '#4f46e5'

/** Ordinal ramp, light to dark, for the four funnel stages. */
export const FUNNEL_RAMP = ['#818cf8', '#6366f1', '#4f46e5', '#3730a3']

/** Ordinal ramp for the status mix. Rejected is off the progression. */
export const STATUS_CHART_COLORS = {
  saved: '#818cf8',
  applied: '#6366f1',
  shortlisted: '#4f46e5',
  interview: '#3730a3',
  selected: '#1e1b4b',
  rejected: '#dc2626',
}

/** Nominal categorical slots, assigned in this fixed order and never cycled. */
export const CHART_CATEGORICAL = [
  '#4f46e5', '#d97706', '#0891b2', '#dc2626',
  '#059669', '#7c3aed', '#db2777', '#65a30d',
]
