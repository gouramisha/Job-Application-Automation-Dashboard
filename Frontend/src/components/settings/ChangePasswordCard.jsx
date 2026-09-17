import { useState } from 'react'
import { auth } from '../../api/endpoints'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import { Button, Card, CardHeader, Field } from '../ui'

export default function ChangePasswordCard() {
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm: '' })
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const toast = useToast()
  const { logout } = useAuth()

  const set = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
    setErrors({})
  }

  async function submit(event) {
    event.preventDefault()
    if (form.new_password !== form.confirm) {
      setErrors({ confirm: 'Passwords do not match.' })
      return
    }

    setSaving(true)
    try {
      await auth.changePassword({
        current_password: form.current_password,
        new_password: form.new_password,
      })
      // Existing tokens stay valid server-side, but signing out is what people
      // expect after changing a password.
      toast.success('Password changed. Please sign in again.')
      setTimeout(logout, 1200)
    } catch (caught) {
      const data = caught.response?.data
      setErrors(
        data && typeof data === 'object'
          ? Object.fromEntries(
              Object.entries(data).map(([key, value]) => [key, Array.isArray(value) ? value[0] : value]),
            )
          : { detail: 'Could not change your password.' },
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader title="Change password" />
      <form onSubmit={submit} className="space-y-4 px-5 py-5">
        {errors.detail && (
          <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {errors.detail}
          </p>
        )}

        <Field label="Current password" error={errors.current_password} required>
          <input type="password" className="input" value={form.current_password}
            onChange={set('current_password')} autoComplete="current-password" required />
        </Field>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="New password" error={errors.new_password} required>
            <input type="password" className="input" value={form.new_password}
              onChange={set('new_password')} autoComplete="new-password" required />
          </Field>
          <Field label="Confirm new password" error={errors.confirm} required>
            <input type="password" className="input" value={form.confirm}
              onChange={set('confirm')} autoComplete="new-password" required />
          </Field>
        </div>

        <div className="flex justify-end">
          <Button type="submit" variant="secondary" loading={saving}>Change password</Button>
        </div>
      </form>
    </Card>
  )
}
