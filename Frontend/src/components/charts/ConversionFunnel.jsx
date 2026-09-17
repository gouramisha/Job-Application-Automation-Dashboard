import { ChartFrame } from './ChartFrame'
import { FUNNEL_RAMP } from '../../lib/constants'

/** The Applied -> Selected funnel.
 *
 *  Drawn as plain divs rather than a Recharts figure: each stage needs its
 *  count, its share of the top stage, and its drop-off from the previous one,
 *  all directly labelled. An SVG bar chart would need three label layers to
 *  say the same thing.
 */
export default function ConversionFunnel({ stages = [] }) {
  const top = stages[0]?.count ?? 0

  return (
    <ChartFrame
      title="Conversion funnel"
      subtitle="How far your applications get"
      empty={top === 0}
      emptyLabel="Once you mark a job as Applied, the funnel will show how far your applications progress."
      height={260}
    >
      <div className="space-y-3 px-3">
        {stages.map((stage, index) => {
          const previous = stages[index - 1]
          const dropOff = previous && previous.count > 0
            ? Math.round(((previous.count - stage.count) / previous.count) * 100)
            : null

          return (
            <div key={stage.stage}>
              <div className="mb-1.5 flex items-baseline justify-between gap-3">
                <span className="text-xs font-medium text-slate-700">{stage.stage}</span>
                <span className="flex items-baseline gap-2 text-xs text-slate-500">
                  {dropOff !== null && dropOff > 0 && (
                    <span className="text-slate-400">−{dropOff}%</span>
                  )}
                  <span className="tabular font-semibold text-slate-900">{stage.count}</span>
                  <span className="tabular w-11 text-right">{stage.percent}%</span>
                </span>
              </div>
              <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.max(stage.percent, stage.count > 0 ? 2 : 0)}%`,
                    backgroundColor: FUNNEL_RAMP[index] ?? FUNNEL_RAMP.at(-1),
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </ChartFrame>
  )
}
