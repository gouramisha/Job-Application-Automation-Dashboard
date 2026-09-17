import {
  Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { AXIS_PROPS, ChartFrame, ChartTooltip, GRID_PROPS } from './ChartFrame'
import { CHART_PRIMARY } from '../../lib/constants'
import { formatDate } from '../../lib/format'

/** Applications sent over time. One series, so one colour and no legend -
 *  the title names it. */
export default function ApplicationsTrend({ points = [], controls, title = 'Applications over time' }) {
  const total = points.reduce((sum, point) => sum + point.applications, 0)

  return (
    <ChartFrame
      title={title}
      subtitle={total ? `${total} applications in this window` : undefined}
      controls={controls}
      empty={total === 0}
      emptyLabel="No applications recorded in this window yet. They will appear here once you start applying."
    >
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={points} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_PRIMARY} stopOpacity={0.22} />
              <stop offset="100%" stopColor={CHART_PRIMARY} stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid {...GRID_PROPS} />
          <XAxis
            dataKey="date"
            {...AXIS_PROPS}
            minTickGap={28}
            tickFormatter={(value) => formatDate(value, { year: undefined })}
          />
          <YAxis {...AXIS_PROPS} allowDecimals={false} width={32} />
          <Tooltip
            cursor={{ stroke: '#94a3b8', strokeWidth: 1 }}
            content={
              <ChartTooltip labelFormatter={(value) => formatDate(value)} />
            }
          />
          <Area
            type="monotone"
            dataKey="applications"
            name="Applications"
            stroke={CHART_PRIMARY}
            strokeWidth={2}
            fill="url(#trendFill)"
            // A visible dot only on hover keeps a 30-point series readable.
            dot={false}
            activeDot={{ r: 4, strokeWidth: 2, stroke: '#fff' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}
