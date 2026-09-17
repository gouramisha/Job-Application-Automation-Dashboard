/** Shared chrome for every chart: title, optional controls, and a consistent
 *  empty state so a chart with no data never renders bare axes. */
export function ChartFrame({ title, subtitle, controls, empty, emptyLabel, height = 280, children }) {
  return (
    <section className="card flex flex-col">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 px-5 py-4">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
          {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
        </div>
        {controls}
      </div>

      {/* minHeight only applies to the empty state - a populated chart sizes
          itself, so a short one does not leave a band of dead space. */}
      <div className="px-2 py-4" style={empty ? { minHeight: height } : undefined}>
        {empty ? (
          <div className="flex h-full min-h-[200px] items-center justify-center px-4 text-center">
            <p className="max-w-xs text-sm text-slate-400">{emptyLabel}</p>
          </div>
        ) : (
          children
        )}
      </div>
    </section>
  )
}

/** One tooltip style for every chart on the site. */
export function ChartTooltip({ active, payload, label, formatter, labelFormatter }) {
  if (!active || !payload?.length) return null

  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-lg">
      <p className="mb-1 text-xs font-medium text-slate-500">
        {labelFormatter ? labelFormatter(label) : label}
      </p>
      {payload.map((entry) => (
        <div key={entry.dataKey ?? entry.name} className="flex items-center gap-2 text-sm">
          <span
            aria-hidden="true"
            className="size-2.5 shrink-0 rounded-sm"
            style={{ backgroundColor: entry.color || entry.payload?.fill }}
          />
          <span className="text-slate-600">{entry.name}</span>
          <span className="tabular ml-auto font-semibold text-slate-900">
            {formatter ? formatter(entry.value) : entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

/** Legend chips. Text stays in ink colours; only the swatch carries hue. */
export function ChartLegend({ items }) {
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 px-5 pb-1">
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-1.5 text-xs text-slate-600">
          <span
            aria-hidden="true"
            className="size-2.5 rounded-sm"
            style={{ backgroundColor: item.color }}
          />
          {item.label}
        </li>
      ))}
    </ul>
  )
}

export const AXIS_PROPS = {
  stroke: '#cbd5e1',
  tick: { fill: '#64748b', fontSize: 11 },
  tickLine: false,
  axisLine: false,
}

export const GRID_PROPS = {
  stroke: '#e2e8f0',
  strokeDasharray: '0',
  vertical: false,
}
