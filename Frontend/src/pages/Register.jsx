import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthShell from '../components/layout/AuthShell'
import { Button, Field } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const EMPTY = {
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  password_confirm: '',
}

export default function Register() {
  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()

  const update = (field) => (event) => {
    setForm({ ...form, [field]: event.target.value })
    if (errors[field]) setErrors({ ...errors, [field]: undefined })
  }

  function validate() {
    const found = {}
    if (!form.email.includes('@')) found.email = 'Enter a valid email address.'
    if (form.password.length < 8) found.password = 'Use at least 8 characters.'
    if (form.password !== form.password_confirm) {
      found.password_confirm = 'Passwords do not match.'
    }
    return found
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const clientErrors = validate()
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors)
      return
    }

    setSubmitting(true)
    try {
      await register(form)
      toast.success('Account created. Welcome to JobTrack.')
      navigate('/', { replace: true })
    } catch (caught) {
      // DRF returns {field: [messages]}; map it straight onto the inputs
      // rather than flattening everything into one banner.
      const data = caught.response?.data
      if (data && typeof data === 'object') {
        setErrors(
          Object.fromEntries(
            Object.entries(data).map(([field, value]) => [field, Array.isArray(value) ? value[0] : value]),
          ),
        )
      } else {
        toast.error('Could not create your account.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Start tracking applications in under a minute."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {errors.detail && (
          <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {errors.detail}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <Field label="First name" error={errors.first_name}>
            <input className="input" value={form.first_name} onChange={update('first_name')} autoComplete="given-name" />
          </Field>
          <Field label="Last name" error={errors.last_name}>
            <input className="input" value={form.last_name} onChange={update('last_name')} autoComplete="family-name" />
          </Field>
        </div>

        <Field label="Email address" error={errors.email} required>
          <input type="email" className="input" value={form.email} onChange={update('email')} autoComplete="email" required />
        </Field>

        <Field
          label="Password"
          error={errors.password}
          hint="At least 8 characters, and not entirely numeric."
          required
        >
          <input
            type="password"
            className="input"
            value={form.password}
            onChange={update('password')}
            autoComplete="new-password"
            required
          />
        </Field>

        <Field label="Confirm password" error={errors.password_confirm} required>
          <input
            type="password"
            className="input"
            value={form.password_confirm}
            onChange={update('password_confirm')}
            autoComplete="new-password"
            required
          />
        </Field>

        <Button type="submit" loading={submitting} className="w-full" size="lg">
          Create account
        </Button>
      </form>
    </AuthShell>
  )
}
