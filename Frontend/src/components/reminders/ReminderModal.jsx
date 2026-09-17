import { useEffect, useState } from 'react'
import { jobs as jobsApi, reminders as remindersApi } from '../../api/endpoints'
import { useApi } from '../../hooks/useApi'
import { useToast } from '../../context/ToastContext'
import { Button, Field, Modal } from '../ui'
import { REMINDER_KINDS } from '../../lib/constants'

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

const EMPTY = { title: '', kind: 'follow_up', due_date: todayISO(), job: '', notes: '' }

export default function ReminderModal({ open, reminder, onClose, onDone }) {
  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const toast = useToast()

  const { data: jobList } = useApi(() => jobsApi.list({ ordering: 'company_name' }), [])

  useEffect(() => {
    setErrors({})
    setForm(
      reminder
        ? {
            title: reminder.title,
            kind: reminder.kind,
            due_date: reminder.due_date,
            job: reminder.job ?? '',
            notes: reminder.notes ?? '',
          }
        : EMPTY,
    )
  }, [reminder, open])

  const set = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  async function submit(event) {
    event?.preventDefault()
    if (!form.title.trim()) {
      setErrors({ title: 'Give the reminder a title.' })
      return
    }

    setSaving(true)
    const payload = { ...form, job: form.job || null }
    try {
      if (reminder) await remindersApi.update(reminder.id, payload)
      else await remindersApi.create(payload)
      toast.success(reminder ? 'Reminder updated.' : 'Reminder created.')
      onDone()
    } catch (caught) {
      const data = caught.response?.data
      if (data && typeof data === 'object') {
        setErrors(Object.fromEntries(
          Object.entries(data).map(([field, value]) => [field, Array.isArray(value) ? value[0] : value]),
        ))
      } else {
        toast.error('Could not save that reminder.')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={reminder ? 'Edit reminder' : 'New reminder'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button loading={saving} onClick={submit}>{reminder ? 'Save changes' : 'Create'}</Button>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4">
        <Field label="Title" error={errors.title} required>
          <input className="input" value={form.title} onChange={set('title')}
            placeholder="Follow up with Acme about the backend role" required />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Type" error={errors.kind}>
            <select className="input" value={form.kind} onChange={set('kind')}>
              {REMINDER_KINDS.map((kind) => (
                <option key={kind.value} value={kind.value}>{kind.label}</option>
              ))}
            </select>
          </Field>
          <Field label="Due date" error={errors.due_date} required>
            <input type="date" className="input" value={form.due_date} onChange={set('due_date')} required />
          </Field>
        </div>

        <Field label="Related job" error={errors.job} hint="Optional - links the reminder to a job in your list.">
          <select className="input" value={form.job} onChange={set('job')}>
            <option value="">Not linked to a job</option>
            {(jobList?.results ?? []).map((job) => (
              <option key={job.id} value={job.id}>{job.company_name} — {job.job_title}</option>
            ))}
          </select>
        </Field>

        <Field label="Notes" error={errors.notes}>
          <textarea className="input min-h-20" value={form.notes} onChange={set('notes')} />
        </Field>
      </form>
    </Modal>
  )
}
