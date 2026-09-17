import { useState } from 'react'
import { applications as applicationsApi, resumes as resumesApi } from '../../api/endpoints'
import { useApi } from '../../hooks/useApi'
import { apiErrorMessage } from '../../api/client'
import { useToast } from '../../context/ToastContext'
import { Button, Field, Modal } from '../ui'

/** Records an application the user submitted themselves, and moves the job
 *  to Applied in the same call. */
export default function QuickApplyModal({ open, job, onClose, onDone }) {
  const [resume, setResume] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const toast = useToast()

  const { data: resumeList } = useApi(() => resumesApi.list(), [], { immediate: open })
  const available = resumeList?.results ?? []

  async function submit() {
    setSaving(true)
    try {
      await applicationsApi.quickApply({
        job: job.id,
        resume: resume || null,
        notes,
      })
      toast.success('Application recorded, and a follow-up scheduled.')
      onDone()
    } catch (caught) {
      toast.error(apiErrorMessage(caught, 'Could not record that application.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Record an application"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button loading={saving} onClick={submit}>Record it</Button>
        </>
      }
    >
      <p className="mb-4 text-sm text-slate-600">
        Logs that you applied to <span className="font-medium text-slate-900">{job?.job_title}</span> at{' '}
        {job?.company_name}, and moves the job to Applied.
      </p>

      <div className="space-y-4">
        <Field label="Resume used" hint={available.length === 0 ? 'You have not uploaded any resumes yet.' : 'Leave blank to use your default.'}>
          <select className="input" value={resume} onChange={(event) => setResume(event.target.value)}>
            <option value="">Default resume</option>
            {available.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}{item.is_default ? ' (default)' : ''}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Notes" hint="Optional - anything worth remembering about this submission.">
          <textarea className="input min-h-20" value={notes} onChange={(event) => setNotes(event.target.value)} />
        </Field>
      </div>
    </Modal>
  )
}
