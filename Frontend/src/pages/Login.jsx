import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import AuthShell from '../components/layout/AuthShell'
import { Button, Field } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { apiErrorMessage } from '../api/client'

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value })

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await login(form)
      // Return the user to wherever the route guard interrupted them.
      navigate(location.state?.from?.pathname || '/', { replace: true })
    } catch (caught) {
      setError(
        caught.response?.status === 401
          ? 'That email and password combination is not recognised.'
          : apiErrorMessage(caught, 'Could not sign you in.'),
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to pick up your job search where you left off."
      footer={
        <>
          Don&apos;t have an account?{' '}
          <Link to="/register" className="font-medium text-brand-600 hover:text-brand-700">
            Create one
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {error && (
          <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        )}

        <Field label="Email address" required>
          <input
            type="email"
            className="input"
            value={form.email}
            onChange={update('email')}
            autoComplete="email"
            required
          />
        </Field>

        <Field label="Password" required>
          <input
            type="password"
            className="input"
            value={form.password}
            onChange={update('password')}
            autoComplete="current-password"
            required
          />
        </Field>

        <Button type="submit" loading={submitting} className="w-full" size="lg">
          Sign in
        </Button>
      </form>

      <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-xs text-slate-600">
        <span className="font-medium text-slate-700">Demo account:</span> demo@example.com / DemoPass123!
      </div>
    </AuthShell>
  )
}
