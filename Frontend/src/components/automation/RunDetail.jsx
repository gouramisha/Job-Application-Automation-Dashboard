import { useState } from 'react'
import { applications as applicationsApi } from '../../api/endpoints'
import { apiErrorMessage } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { Button, Spinner } from '../ui'
import { RunStatusBadge } from '../StatusBadge'

const LOG_TONES = {
  debug: 'text-slate-400',
  info: 'text-slate-600',
  warning: 'text-amber-700',
  error: 'text-rose-700',
}

export default function RunDetail({ run, onChanged }) {
  const [marking, setMarking] = useState(false)
  const toast = useToast()

  const filled = Object.entries(run.fields_filled || {})
  const skipped = run.fields_skipped || []
  const unanswered = run.unanswered_questions || []

  async function markSubmitted() {
    setMarking(true)
    try {
      await applicationsApi.markSubmitted(run.application)
      toast.success('Recorded as submitted, and a follow-up scheduled.')
      onChanged?.()
    } catch (caught) {
      toast.error(apiErrorMessage(caught, 'Could not record that.'))
    } finally {
      setMarking(false)
    }
  }

  return (
    <div className="rounded-lg border border-slate-200">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
        <div className="flex items-center gap-2">
          {!run.is_terminal && <Spinner className="size-4 text-slate-400" />}
          <RunStatusBadge status={run.status} label={run.status_display} />
          <span className="text-xs text-slate-500">
            {run.filled_count} {run.filled_count === 1 ? 'field' : 'fields'} filled
            {run.resume_uploaded && ' · resume attached'}
          </span>
        </div>

        {/* The user pressed Submit on the site themselves; this is how the
            tracker learns that it actually went out. */}
        {run.status === 'awaiting_review' && run.application && (
          <Button size="sm" loading={marking} onClick={markSubmitted}>
            I submitted this
          </Button>
        )}
      </div>

      {run.stop_reason && (
        <p className="border-b border-slate-100 px-4 py-2.5 text-sm text-slate-600">{run.stop_reason}</p>
      )}

      {run.error_message && (
        <p className="border-b border-slate-100 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
          {run.error_message}
        </p>
      )}

      <div className="space-y-3 px-4 py-3">
        {filled.length > 0 && (
          <Section title={`Filled (${filled.length})`}>
            <dl className="grid gap-x-4 gap-y-1 sm:grid-cols-2">
              {filled.map(([field, value]) => (
                <div key={field} className="flex gap-2 text-xs">
                  <dt className="shrink-0 text-slate-400">{field.replaceAll('_', ' ')}</dt>
                  <dd className="truncate text-slate-700">{String(value)}</dd>
                </div>
              ))}
            </dl>
          </Section>
        )}

        {unanswered.length > 0 && (
          <Section title={`Needs your answer (${unanswered.length})`}>
            <ul className="space-y-1 text-xs text-amber-800">
              {unanswered.map((question) => <li key={question}>• {question}</li>)}
            </ul>
            <p className="mt-2 text-xs text-slate-500">
              Save these on your Profile under saved answers and the next run will fill them.
            </p>
          </Section>
        )}

        {skipped.length > 0 && (
          <details className="text-xs">
            <summary className="cursor-pointer text-slate-500 transition hover:text-slate-700">
              Skipped ({skipped.length})
            </summary>
            <ul className="mt-1.5 space-y-1 text-slate-500">
              {skipped.map((item, index) => (
                <li key={`${item.label}-${index}`}>
                  <span className="text-slate-700">{item.label}</span> — {item.reason}
                </li>
              ))}
            </ul>
          </details>
        )}

        {run.screenshot_url && (
          <details className="text-xs">
            <summary className="cursor-pointer text-slate-500 transition hover:text-slate-700">
              Screenshot of the filled form
            </summary>
            <img src={run.screenshot_url} alt="The application form after automated filling"
              className="mt-2 w-full rounded-lg border border-slate-200" />
          </details>
        )}

        {run.logs?.length > 0 && (
          <details className="text-xs">
            <summary className="cursor-pointer text-slate-500 transition hover:text-slate-700">
              Run log ({run.logs.length} steps)
            </summary>
            <ol className="mt-1.5 space-y-0.5 font-mono">
              {run.logs.map((entry) => (
                <li key={entry.id} className={LOG_TONES[entry.level]}>{entry.message}</li>
              ))}
            </ol>
          </details>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold text-slate-700">{title}</h4>
      {children}
    </div>
  )
}
