import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { jobs as jobsApi } from '../api/endpoints'
import { useApi } from '../hooks/useApi'
import { useToast } from '../context/ToastContext'
import { Button, Card, CardHeader, Field, PageLoader } from '../components/ui'
import { JOB_STATUSES } from '../lib/constants'

const EMPTY = {
  company_name: '', job_title: '', location: '', job_url: '', salary: '',
  experience_required: '', skills: '', job_description: '', source: 'other',
  status: 'saved', applied_date: '', notes: '', is_remote: false,
}

export default function AddJob() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const toast = useToast()

  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)

  const { data: options } = useApi(() => jobsApi.options(), [])
  const { data: existing, loading } = useApi(
    () => jobsApi.get(id),
    [id],
    { immediate: isEdit },
  )

  useEffect(() => {
    if (!existing) return
    setForm({
      ...EMPTY,
      ...existing,
      // A null date from the API would make the input uncontrolled.
      applied_date: existing.applied_date || '',
    })
  }, [existing])

  const set = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value
    setForm((current) => ({ ...current, [field]: value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!form.company_name.trim() || !form.job_title.trim()) {
      setErrors({
        company_name: form.company_name.trim() ? undefined : 'Company name is required.',
        job_title: form.job_title.trim() ? undefined : 'Job title is required.',
      })
      return
    }

    setSaving(true)
    const payload = { ...form, applied_date: form.applied_date || null }
    try {
      const response = isEdit
        ? await jobsApi.update(id, payload)
        : await jobsApi.create(payload)
      toast.success(isEdit ? 'Job updated.' : 'Job added.')
      navigate(`/jobs/${response.data.id}`)
    } catch (caught) {
      const data = caught.response?.data
      if (data && typeof data === 'object') {
        setErrors(Object.fromEntries(
          Object.entries(data).map(([field, value]) => [field, Array.isArray(value) ? value[0] : value]),
        ))
        toast.error('Please fix the highlighted fields.')
      } else {
        toast.error('Could not save that job.')
      }
    } finally {
      setSaving(false)
    }
  }

  if (isEdit && loading) return <PageLoader label="Loading job" />

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-3xl space-y-5" noValidate>
      <Card>
        <CardHeader title={isEdit ? 'Edit job' : 'Add a job'} subtitle="Only company and title are required - fill in the rest as you learn it." />

        <div className="space-y-4 px-5 py-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Company name" error={errors.company_name} required>
              <input className="input" value={form.company_name} onChange={set('company_name')} required />
            </Field>
            <Field label="Job title" error={errors.job_title} required>
              <input className="input" value={form.job_title} onChange={set('job_title')} required />
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Location" error={errors.location}>
              <input className="input" value={form.location} onChange={set('location')} placeholder="Bengaluru, India" />
            </Field>
            <Field label="Salary" error={errors.salary} hint="Free text - '18-24 LPA', '$120k', 'Not disclosed'.">
              <input className="input" value={form.salary} onChange={set('salary')} />
            </Field>
          </div>

          <Field
            label="Application URL"
            error={errors.job_url}
            hint="The automation module opens this page to fill the form."
          >
            <input type="url" className="input" value={form.job_url} onChange={set('job_url')} placeholder="https://boards.greenhouse.io/…" />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Experience required" error={errors.experience_required} hint="'3-5 years' or '5+' - used for match scoring.">
              <input className="input" value={form.experience_required} onChange={set('experience_required')} />
            </Field>
            <Field label="Source" error={errors.source}>
              <select className="input" value={form.source} onChange={set('source')}>
                {(options?.sources ?? []).map((source) => (
                  <option key={source.value} value={source.value}>{source.label}</option>
                ))}
              </select>
            </Field>
          </div>

          <Field label="Skills" error={errors.skills} hint="Comma separated. Overlap with your profile skills feeds the match score.">
            <input className="input" value={form.skills} onChange={set('skills')} placeholder="Python, Django, PostgreSQL" />
          </Field>

          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={form.is_remote} onChange={set('is_remote')}
              className="size-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
            This is a remote role
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Status" error={errors.status}>
              <select className="input" value={form.status} onChange={set('status')}>
                {JOB_STATUSES.map((status) => (
                  <option key={status.value} value={status.value}>{status.label}</option>
                ))}
              </select>
            </Field>
            <Field
              label="Applied date"
              error={errors.applied_date}
              hint="Left blank, this is set automatically the day you mark it as applied."
            >
              <input type="date" className="input" value={form.applied_date} onChange={set('applied_date')} />
            </Field>
          </div>

          <Field label="Job description" error={errors.job_description}>
            <textarea className="input min-h-28" value={form.job_description} onChange={set('job_description')} />
          </Field>

          <Field label="Notes" error={errors.notes} hint="Private to you - referrals, recruiter names, anything worth remembering.">
            <textarea className="input min-h-20" value={form.notes} onChange={set('notes')} />
          </Field>
        </div>
      </Card>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={() => navigate(-1)}>Cancel</Button>
        <Button type="submit" loading={saving}>{isEdit ? 'Save changes' : 'Add job'}</Button>
      </div>
    </form>
  )
}
