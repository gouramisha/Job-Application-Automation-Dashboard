import { useCallback, useEffect, useRef, useState } from 'react'
import { automation, resumes as resumesApi } from '../../api/endpoints'
import { useApi } from '../../hooks/useApi'
import { apiErrorMessage } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { Button, Card, CardHeader, Field } from '../ui'
import RunDetail from './RunDetail'

const POLL_MS = 2500

/** Starts and monitors a form-fill run for one job.
 *
 *  The worker owns the browser, so this panel polls the run until it reaches
 *  a terminal state rather than holding a request open.
 */
export default function AutomationPanel({ job, onRunFinished }) {
  const [resume, setResume] = useState('')
  const [starting, setStarting] = useState(false)
  const [activeRun, setActiveRun] = useState(null)
  const toast = useToast()
  const pollRef = useRef(null)

  const { data: resumeList } = useApi(() => resumesApi.list(), [])
  const { data: preflight } = useApi(
    () => automation.preflight(job.job_url),
    [job.job_url],
    { immediate: Boolean(job.job_url) },
  )
  const { data: history, reload: reloadHistory } = useApi(
    () => automation.runs({ job: job.id }),
    [job.id],
  )

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  // Poll while a run is live; always tear the interval down on unmount so a
  // navigation away does not leave a timer firing against a dead component.
  useEffect(() => {
    if (!activeRun || activeRun.is_terminal) {
      stopPolling()
      return undefined
    }
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await automation.run(activeRun.id)
        setActiveRun(data)
        if (data.is_terminal) {
          stopPolling()
          reloadHistory()
          onRunFinished?.()
          if (data.status === 'failed') toast.error('The automation run failed. See the log below.')
          else if (data.status === 'awaiting_review') toast.success('Form filled. Review it and press Submit yourself.')
        }
      } catch {
        stopPolling()
      }
    }, POLL_MS)
    return stopPolling
  }, [activeRun, stopPolling, reloadHistory, onRunFinished, toast])

  async function start() {
    setStarting(true)
    try {
      const { data } = await automation.start({ job: job.id, resume: resume || null })
      setActiveRun(data)
      reloadHistory()
      if (data.status === 'unsupported') {
        toast.error('That site is not on the supported list yet.')
      } else {
        toast.info('Run queued. Make sure the automation worker is running.')
      }
    } catch (caught) {
      toast.error(apiErrorMessage(caught, 'Could not start the run.'))
    } finally {
      setStarting(false)
    }
  }

  const runs = history?.results ?? []
  const latestSummary = runs[0]

  // The list endpoint omits the step log to keep the payload small, so pull
  // the detail for whichever run is being shown. Without this the log and its
  // skipped-field breakdown vanish on a page reload.
  const { data: latestDetail } = useApi(
    () => automation.run(latestSummary.id),
    [latestSummary?.id],
    { immediate: Boolean(latestSummary && !activeRun) },
  )

  const latest = activeRun || latestDetail || latestSummary
  const supported = preflight?.supported
  const available = resumeList?.results ?? []

  return (
    <Card>
      <CardHeader
        title="Assisted form filling"
        subtitle="Fills what it can from your profile, then hands the form back to you"
      />

      <div className="space-y-4 px-5 py-4">
        {!job.job_url ? (
          <Notice tone="neutral">
            Add an application URL to this job to use assisted filling.
          </Notice>
        ) : (
          <>
            <PolicyNotice preflight={preflight} />

            {supported && (
              <>
                <Field label="Resume to attach" hint={available.length === 0 ? 'Upload a resume first and it will be attached automatically.' : undefined}>
                  <select className="input" value={resume} onChange={(event) => setResume(event.target.value)}>
                    <option value="">Default resume</option>
                    {available.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}{item.is_default ? ' (default)' : ''}
                      </option>
                    ))}
                  </select>
                </Field>

                <Button
                  onClick={start}
                  loading={starting || (latest && !latest.is_terminal)}
                  disabled={latest && !latest.is_terminal}
                >
                  {latest && !latest.is_terminal ? 'Run in progress…' : 'Start assisted fill'}
                </Button>
              </>
            )}
          </>
        )}

        {latest && <RunDetail run={latest} onChanged={() => { reloadHistory(); onRunFinished?.() }} />}

        {runs.length > 1 && (
          <details className="text-sm">
            <summary className="cursor-pointer text-slate-500 transition hover:text-slate-700">
              {runs.length - 1} earlier {runs.length - 1 === 1 ? 'run' : 'runs'}
            </summary>
            <ul className="mt-2 space-y-1.5">
              {runs.slice(1).map((run) => (
                <li key={run.id} className="flex justify-between text-xs text-slate-500">
                  <span>{run.status_display}</span>
                  <span>{new Date(run.created_at).toLocaleString()}</span>
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </Card>
  )
}

function PolicyNotice({ preflight }) {
  if (!preflight) return null

  if (!preflight.supported) {
    return (
      <Notice tone="warning">
        <strong className="font-medium">This site is not supported yet.</strong> Assisted filling only
        runs on hosts that have been reviewed and added to the allowlist. You can still apply manually
        and record it here.
      </Notice>
    )
  }

  return (
    <Notice tone={preflight.will_auto_submit ? 'info' : 'neutral'}>
      <strong className="font-medium">{preflight.site?.name} is supported.</strong>{' '}
      {preflight.submit_policy}
    </Notice>
  )
}

function Notice({ tone = 'neutral', children }) {
  const tones = {
    neutral: 'border-slate-200 bg-slate-50 text-slate-700',
    info: 'border-brand-200 bg-brand-50 text-brand-900',
    warning: 'border-amber-200 bg-amber-50 text-amber-900',
  }
  return <div className={`rounded-lg border px-3 py-2.5 text-sm leading-relaxed ${tones[tone]}`}>{children}</div>
}
