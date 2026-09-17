import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AXIS_PROPS, ChartFrame, ChartTooltip } from './ChartFrame'
import { STATUS_CHART_COLORS } from '../../lib/constants'

/** Where every tracked job currently sits.
 *
 *  A horizontal bar rather than a pie: six segments is at the limit for
 *  part-to-whole, and several of these counts are usually close, which is
 *  exactly what a pie hides.
 */
export default function StatusMix({ rows = [], title = 'Status breakdown' }) {
  const data = rows.map((row) => ({
    ...row,
    fill: STATUS_CHART_COLORS[row.key] ?? STATUS_CHART_COLORS.saved,
  }))
  const total = data.reduce((sum, row) => sum + row.count, 0)

  return (
    <ChartFrame
      title={title}
      subtitle={total ? `${total} jobs tracked` : undefined}
      empty={total === 0}
      emptyLabel="Add a few jobs and their status mix will show up here."
    >
      <ResponsiveContainer width="100%" height={Math.max(data.length * 38, 200)}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 40, left: 8, bottom: 0 }}>
          <XAxis type="number" hide allowDecimals={false} />
          <YAxis type="category" dataKey="label" width={88} {...AXIS_PROPS} />
          <Tooltip cursor={{ fill: '#f1f5f9' }} content={<ChartTooltip />} />
          <Bar
            dataKey="count"
            name="Jobs"
            radius={[0, 4, 4, 0]}
            barSize={16}
            label={{ position: 'right', fill: '#475569', fontSize: 11 }}
          >
            {data.map((row) => (
              <Cell key={row.key} fill={row.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  )
}
