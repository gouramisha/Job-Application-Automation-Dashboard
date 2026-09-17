import { useEffect, useState } from 'react'
import { auth } from '../api/endpoints'
import { useApi } from '../hooks/useApi'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { Button, Card, CardHeader, Field, PageLoader } from '../components/ui'
import CustomAnswers from '../components/profile/CustomAnswers'

const WORK_AUTH = [
  { value: 'citizen', label: 'Citizen' },
  { value: 'permanent_resident', label: 'Permanent resident' },
  { value: 'work_visa', label: 'Work visa' },
  { value: 'student_visa', label: 'Student visa' },
  { value: 'needs_sponsorship', label: 'Needs sponsorship' },
  { value: 'other', label: 'Other' },
]

export default function Profile() {
  const [form, setForm] = useState(null)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const toast = useToast()
  const { refreshUser } = useAuth()

  const { data, loading } = useApi(() => auth.profile(), [])

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  const set = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value
    setForm((current) => ({ ...current, [field]: value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  async function save(event) {
    event.preventDefault()
    setSaving(true)
    // Blank number inputs must go back as null, not '' - DRF rejects the
    // empty string for an integer field.
    const payload = {
      ...form,
      expected_salary_min: form.expected_salary_min || null,
      expected_salary_max: form.expected_salary_max || null,
      years_experience: form.years_experience || 0,
      notice_period_days: form.notice_period_days || 0,
    }
    try {
      const response = await auth.updateProfile(payload)
      setForm(response.data)
      await refreshUser()
      toast.success('Profile saved.')
      setErrors({})
    } catch (caught) {
      const body = caught.response?.data
      if (body && typeof body === 'object') {
        setErrors(Object.fromEntries(
          Object.entries(body).map(([field, value]) => [field, Array.isArray(value) ? value[0] : value]),
        ))
        toast.error('Please fix the highlighted fields.')
      } else {
        toast.error('Could not save your profile.')
      }
    } finally {
      setSaving(false)
    }
  }

  if (loading || !form) return <PageLoader label="Loading your profile" />

  return (
    <form onSubmit={save} className="mx-auto max-w-3xl space-y-5">
      <div className="rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-900">
        These details are what assisted form filling types into application forms. The more you fill
        in here, the less you type on each application.
      </div>

      <Card>
        <CardHeader title="About you" />
        <div className="space-y-4 px-5 py-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="First name" error={errors.first_name}>
              <input className="input" value={form.first_name ?? ''} onChange={set('first_name')} />
            </Field>
            <Field label="Last name" error={errors.last_name}>
              <input className="input" value={form.last_name ?? ''} onChange={set('last_name')} />
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Email">
              <input className="input" value={form.email ?? ''} disabled />
            </Field>
            <Field label="Phone" error={errors.phone}>
              <input className="input" value={form.phone ?? ''} onChange={set('phone')} />
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="City" error={errors.city}>
              <input className="input" value={form.city ?? ''} onChange={set('city')} />
            </Field>
            <Field label="State" error={errors.state}>
              <input className="input" value={form.state ?? ''} onChange={set('state')} />
            </Field>
            <Field label="Country" error={errors.country}>
              <input className="input" value={form.country ?? ''} onChange={set('country')} />
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="LinkedIn" error={errors.linkedin_url}>
              <input type="url" className="input" value={form.linkedin_url ?? ''} onChange={set('linkedin_url')} />
            </Field>
            <Field label="GitHub" error={errors.github_url}>
              <input type="url" className="input" value={form.github_url ?? ''} onChange={set('github_url')} />
            </Field>
            <Field label="Portfolio" error={errors.portfolio_url}>
              <input type="url" className="input" value={form.portfolio_url ?? ''} onChange={set('portfolio_url')} />
            </Field>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="Experience" subtitle="Used for match scoring and to answer screening questions" />
        <div className="space-y-4 px-5 py-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Current title" error={errors.current_title}>
              <input className="input" value={form.current_title ?? ''} onChange={set('current_title')} />
            </Field>
            <Field label="Current company" error={errors.current_company}>
              <input className="input" value={form.current_company ?? ''} onChange={set('current_company')} />
            </Field>
            <Field label="Years of experience" error={errors.years_experience}>
              <input type="number" step="0.5" min="0" className="input"
                value={form.years_experience ?? ''} onChange={set('years_experience')} />
            </Field>
          </div>

          <Field label="Skills" error={errors.skills}
            hint="Comma separated. Overlap with a job's skills raises its match score.">
            <input className="input" value={form.skills ?? ''} onChange={set('skills')}
              placeholder="Python, Django, PostgreSQL, React" />
          </Field>

          <Field label="Professional summary" error={errors.summary}
            hint="Reused for 'tell us about yourself' and cover-letter boxes.">
            <textarea className="input min-h-24" value={form.summary ?? ''} onChange={set('summary')} />
          </Field>
        </div>
      </Card>

      <Card>
        <CardHeader title="What you are looking for" subtitle="Drives the match scores on your Jobs page" />
        <div className="space-y-4 px-5 py-5">
          <Field label="Target roles" error={errors.desired_roles} hint="Comma separated job titles.">
            <input className="input" value={form.desired_roles ?? ''} onChange={set('desired_roles')}
              placeholder="Backend Engineer, Python Developer" />
          </Field>

          <Field label="Target locations" error={errors.desired_locations} hint="Comma separated cities.">
            <input className="input" value={form.desired_locations ?? ''} onChange={set('desired_locations')}
              placeholder="Bengaluru, Pune, Remote" />
          </Field>

          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" checked={form.open_to_remote ?? false} onChange={set('open_to_remote')}
                className="size-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
              Open to remote roles
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" checked={form.willing_to_relocate ?? false} onChange={set('willing_to_relocate')}
                className="size-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
              Willing to relocate
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-4">
            <Field label="Salary from" error={errors.expected_salary_min}>
              <input type="number" min="0" className="input"
                value={form.expected_salary_min ?? ''} onChange={set('expected_salary_min')} />
            </Field>
            <Field label="Salary to" error={errors.expected_salary_max}>
              <input type="number" min="0" className="input"
                value={form.expected_salary_max ?? ''} onChange={set('expected_salary_max')} />
            </Field>
            <Field label="Currency" error={errors.salary_currency}>
              <input className="input" value={form.salary_currency ?? ''} onChange={set('salary_currency')} />
            </Field>
            <Field label="Notice (days)" error={errors.notice_period_days}>
              <input type="number" min="0" className="input"
                value={form.notice_period_days ?? ''} onChange={set('notice_period_days')} />
            </Field>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Work authorisation" error={errors.work_authorization}>
              <select className="input" value={form.work_authorization ?? 'citizen'} onChange={set('work_authorization')}>
                {WORK_AUTH.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Sponsorship">
              <label className="mt-2 flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={form.requires_sponsorship ?? false} onChange={set('requires_sponsorship')}
                  className="size-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
                I need visa sponsorship
              </label>
            </Field>
          </div>
        </div>
      </Card>

      <CustomAnswers
        value={form.custom_answers ?? {}}
        onChange={(answers) => setForm((current) => ({ ...current, custom_answers: answers }))}
      />

      <div className="sticky bottom-4 flex justify-end">
        <Button type="submit" loading={saving} size="lg" className="shadow-lg">Save profile</Button>
      </div>
    </form>
  )
}
