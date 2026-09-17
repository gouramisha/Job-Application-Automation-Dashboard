import { useEffect, useState } from 'react'
import { auth, automation } from '../api/endpoints'
import { useApi } from '../hooks/useApi'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, CardHeader, Field, PageLoader } from '../components/ui'
import ChangePasswordCard from '../components/settings/ChangePasswordCard'

export default function Settings() {
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const toast = useToast()

  const { data } = useApi(() => auth.settings(), [])
  const { data: sites } = useApi(() => automation.sites(), [])

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  const set = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value
    setForm((current) => ({ ...current, [field]: value }))
  }

  async function save(event) {
    event.preventDefault()
    setSaving(true)
    try {
      const response = await auth.updateSettings({
        ...form,
        reminder_lead_days: Number(form.reminder_lead_days) || 0,
        default_follow_up_days: Number(form.default_follow_up_days) || 7,
      })
      setForm(response.data)
      toast.success('Settings saved.')
    } catch {
      toast.error('Could not save your settings.')
    } finally {
      setSaving(false)
    }
  }

  if (!form) return <PageLoader label="Loading settings" />

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <form onSubmit={save} className="space-y-5">
        <Card>
          <CardHeader title="Reminders" subtitle="How follow-ups get scheduled" />
          <div className="space-y-4 px-5 py-5">
            <label className="flex items-start gap-3">
              <input type="checkbox" checked={form.auto_create_follow_ups} onChange={set('auto_create_follow_ups')}
                className="mt-0.5 size-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
              <span className="text-sm">
                <span className="font-medium text-slate-800">Schedule follow-ups automatically</span>
                <span className="mt-0.5 block text-slate-500">
                  Creates a follow-up reminder whenever you record an application.
                </span>
              </span>
            </label>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Follow up after (days)" hint="How long to wait before the nudge.">
                <input type="number" min="1" max="90" className="input"
                  value={form.default_follow_up_days} onChange={set('default_follow_up_days')} />
              </Field>
              <Field label="Show as upcoming (days before)" hint="How early a reminder appears on the dashboard.">
                <input type="number" min="0" max="30" className="input"
                  value={form.reminder_lead_days} onChange={set('reminder_lead_days')} />
              </Field>
            </div>

            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" checked={form.email_reminders} onChange={set('email_reminders')}
                className="size-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
              Email me about due reminders
            </label>
          </div>
        </Card>

        <Card>
          <CardHeader title="Automation" subtitle="What the form filler is allowed to do" />
          <div className="space-y-4 px-5 py-5">
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-relaxed text-slate-700">
              Assisted filling types your saved details into an application form and attaches your
              resume, then stops and hands the browser to you. It does not press Submit.
              <span className="mt-2 block">
                The only exception is a site that publishes an official application API. For those,
                and only with the switch below turned on, a run may submit on your behalf.
              </span>
            </div>

            <label className="flex items-start gap-3">
              <input type="checkbox" checked={form.allow_auto_submit} onChange={set('allow_auto_submit')}
                className="mt-0.5 size-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500" />
              <span className="text-sm">
                <span className="font-medium text-slate-800">
                  Allow automated submission where officially supported
                </span>
                <span className="mt-0.5 block text-slate-500">
                  Applies only to allowlisted sites with a documented application API. Every other
                  site still stops before Submit, whatever this is set to.
                </span>
              </span>
            </label>
          </div>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" loading={saving}>Save settings</Button>
        </div>
      </form>

      <Card>
        <CardHeader title="Supported sites" subtitle="Hosts reviewed and approved for assisted filling" />
        <div className="px-5 py-4">
          {!sites?.length ? (
            <p className="text-sm text-slate-500">
              No sites configured yet. Run{' '}
              <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">python manage.py seed_sites</code>{' '}
              to add the common ones.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {sites.map((site) => (
                <li key={site.id} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800">{site.name}</p>
                    <p className="truncate text-xs text-slate-500">{site.domain}</p>
                  </div>
                  {site.auto_submit_eligible ? (
                    <Badge className="bg-emerald-50 text-emerald-700 ring-emerald-200">Official API</Badge>
                  ) : (
                    <Badge className="bg-slate-100 text-slate-600 ring-slate-200">You press Submit</Badge>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </Card>

      <ChangePasswordCard />
    </div>
  )
}
