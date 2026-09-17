import { Link } from 'react-router-dom'

/** A single number with its label. Deliberately not a chart - one value is
 *  read fastest as a number, and a one-bar chart says less, not more. */
export default function StatTile({ label, value, sublabel, tone = 'default', to }) {
  const tones = {
    default: 'text-slate-900',
    brand: 'text-brand-700',
    positive: 'text-emerald-700',
    warning: 'text-amber-700',
    negative: 'text-rose-700',
  }

  const body = (
    <>
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className={`tabular mt-1.5 text-2xl font-semibold ${tones[tone]}`}>{value}</p>
      {sublabel && <p className="mt-1 text-xs text-slate-400">{sublabel}</p>}
    </>
  )

  const className = 'card px-4 py-3.5'
  if (!to) return <div className={className}>{body}</div>

  return (
    <Link to={to} className={`${className} block transition hover:border-brand-300 hover:shadow-md`}>
      {body}
    </Link>
  )
}
