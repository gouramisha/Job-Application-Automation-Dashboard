import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AXIS_PROPS, ChartFrame, ChartTooltip, GRID_PROPS } from './ChartFrame'
import { CHART_PRIMARY } from '../../lib/constants'

/** Counts across nominal categories - sources, companies, methods.
 *
 *  One series, so every bar is the same hue. Shading each bar by its own value
 *  would encode the length twice and add nothing the axis does not already say.
 */
export default function CategoryBars({ rows = [], title, subtitle, emptyLabel, limit = 8 }) {
  const data = rows.slice(0, limit)

  return (
    <ChartFrame
      title={title}
      subtitle={subtitle}
      empty={data.length === 0}
      emptyLabel={emptyLabel}
    >
      <ResponsiveContainer width="100%" height={Math.max(data.length * 36, 200)}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 40, left: 8, bottom: 0 }}>
          <CartesianGrid {...GRID_PROPS} horizontal={false} vertical />
          <XAxis type="number" {...AXIS_PROPS} allowDecimals={false} />
          <YAxis type="category" dataKey="label" width={110} {...AXIS_PROPS} />
          <Tooltip cursor={{ fill: '#f1f5f9' }} content={<ChartTooltip />} />
          <Bar
            dataKey="count"
            name="Jobs"
            fill={CHART_PRIMARY}
            radius={[0, 4, 4, 0]}
            barSize={16}
            label={{ position: 'right', fill: '#475569', fontSize: 11 }}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}
