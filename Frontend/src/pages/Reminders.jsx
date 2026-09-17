import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { reminders as remindersApi } from '../api/endpoints'
import { useApi } from '../hooks/useApi'
import { apiErrorMessage } from '../api/client'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, EmptyState, PageLoader } from '../components/ui'
import ReminderModal from '../components/reminders/ReminderModal'
import { formatDate, relativeDate } from '../lib/format'

const VIEWS = [
  { key: 'open', label: 'Open', params: { is_done: false, ordering: 'due_date' } },
  { key: 'overdue', label: 'Overdue', params: { overdue: true, ordering: 'due_date' } },
  { key: 'done', label: 'Completed', params: { is_done: true, ordering: '-due_date' } },
  { key: 'all', label: 'All', params: { ordering: 'due_date' } },
]

export default function Reminders() {
  const [view, setView] = useState('open')
  const [editing, setEditing] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const toast = useToast()

  const params = useMemo(() => VIEWS.find((item) => item.key === view).params, [view])
  const { data, loading, error, reload } = useApi(() => remindersApi.list(params), [params])

  async function toggle(reminder) {
    try {
      await (reminder.is_done ? remindersApi.reopen(reminder.id) : remindersApi.complete(reminder.id))
      reload()
    } catch (caught) {
      toast.error(apiErrorMessage(caught))
    }
  }

  async function remove(reminder) {
    if (!window.confirm(`Delete "${reminder.title}"?`)) return
    try {
      await remindersApi.remove(reminder.id)
      toast.success('Reminder deleted.')
      reload()
    } catch (caught) {
      toast.error(apiErrorMessage(caught))
    }
  }

  const rows = data?.results ?? []

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-lg bg-slate-100 p-0.5">
          {VIEWS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setView(item.key)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                view === item.key ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
        <Button onClick={() => { setEditing(null); setModalOpen(true) }}>+ New reminder</Button>
      </div>

      {error ? (
        <Card>
          <EmptyState icon="⚠" title="Could not load reminders" description={error}
            action={<Button onClick={reload}>Try again</Button>} />
        </Card>
      ) : loading && !data ? (
        <PageLoader label="Loading reminders" />
      ) : rows.length === 0 ? (
        <Card>
          <EmptyState
            icon={view === 'done' ? '📭' : '✓'}
            title={view === 'overdue' ? 'Nothing overdue' : view === 'done' ? 'Nothing completed yet' : 'You are all caught up'}
            description="Follow-ups schedule themselves when you record an application. You can add your own for interviews and deadlines."
            action={<Button onClick={() => { setEditing(null); setModalOpen(true) }}>Add a reminder</Button>}
          />
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <ul className="divide-y divide-slate-100">
            {rows.map((reminder) => (
              <li key={reminder.id} className="flex items-start gap-3 px-5 py-3.5 transition hover:bg-slate-50">
                <input
                  type="checkbox"
                  checked={reminder.is_done}
                  onChange={() => toggle(reminder)}
                  aria-label={reminder.is_done ? `Reopen ${reminder.title}` : `Complete ${reminder.title}`}
                  className="mt-0.5 size-4 shrink-0 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />

                <div className="min-w-0 flex-1">
                  <p className={`text-sm font-medium ${reminder.is_done ? 'text-slate-400 line-through' : 'text-slate-900'}`}>
                    {reminder.title}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
                    <Badge className="bg-slate-50 text-slate-600 ring-slate-200">{reminder.kind_display}</Badge>
                    {reminder.job && (
                      <Link to={`/jobs/${reminder.job}`} className="text-brand-600 hover:text-brand-700">
                        {reminder.company_name}
                      </Link>
                    )}
                    <span title={formatDate(reminder.due_date)} className={reminder.is_overdue ? 'font-medium text-rose-600' : ''}>
                      {reminder.is_overdue ? 'Overdue · ' : ''}{relativeDate(reminder.due_date)}
                    </span>
                  </div>
                  {reminder.notes && <p className="mt-1 text-xs text-slate-500">{reminder.notes}</p>}
                </div>

                <div className="flex shrink-0 gap-2">
                  <button
                    type="button"
                    onClick={() => { setEditing(reminder); setModalOpen(true) }}
                    className="text-xs font-medium text-slate-500 transition hover:text-brand-600"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => remove(reminder)}
                    className="text-xs font-medium text-slate-400 transition hover:text-rose-600"
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}

      <ReminderModal
        open={modalOpen}
        reminder={editing}
        onClose={() => setModalOpen(false)}
        onDone={() => { setModalOpen(false); reload() }}
      />
    </div>
  )
}
