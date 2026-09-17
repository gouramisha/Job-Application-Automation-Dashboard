import { useRef, useState } from 'react'
import { resumes as resumesApi } from '../../api/endpoints'
import { useToast } from '../../context/ToastContext'
import { Button, Field, Modal } from '../ui'

const EMPTY = { name: '', target_role: '', notes: '', is_default: false }

export default function UploadResumeModal({ open, onClose, onDone, isFirst }) {
  const [form, setForm] = useState(EMPTY)
  const [file, setFile] = useState(null)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const fileInput = useRef(null)
  const toast = useToast()

  const set = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value
    setForm((current) => ({ ...current, [field]: value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  function pickFile(event) {
    const picked = event.target.files?.[0] || null
    setFile(picked)
    setErrors((current) => ({ ...current, file: undefined }))
    // Default the label to the filename, so a hurried upload still gets a
    // name the user recognises later.
    if (picked && !form.name) {
      setForm((current) => ({ ...current, name: picked.name.replace(/\.[^.]+$/, '') }))
    }
  }

  function reset() {
    setForm(EMPTY)
    setFile(null)
    setErrors({})
    if (fileInput.current) fileInput.current.value = ''
  }

  async function submit(event) {
    event?.preventDefault()
    if (!file) {
      setErrors({ file: 'Choose a file to upload.' })
      return
    }

    const payload = new FormData()
    payload.append('file', file)
    Object.entries(form).forEach(([key, value]) => payload.append(key, value))

    setSaving(true)
    try {
      await resumesApi.create(payload)
      toast.success('Resume uploaded.')
      reset()
      onDone()
    } catch (caught) {
      const data = caught.response?.data
      if (data && typeof data === 'object') {
        setErrors(Object.fromEntries(
          Object.entries(data).map(([field, value]) => [field, Array.isArray(value) ? value[0] : value]),
        ))
      } else {
        toast.error('Could not upload that resume.')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={() => { reset(); onClose() }}
      title="Upload a resume"
      footer={
        <>
          <Button variant="secondary" onClick={() => { reset(); onClose() }}>Cancel</Button>
          <Button loading={saving} onClick={submit}>Upload</Button>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4">
        <Field label="File" error={errors.file} hint="PDF, DOC, DOCX, RTF or TXT. Up to 10 MB." required>
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.doc,.docx,.rtf,.txt"
            onChange={pickFile}
            className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0
              file:bg-brand-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-brand-700
              hover:file:bg-brand-100"
          />
        </Field>

        <Field label="Name" error={errors.name} hint="How you will recognise this version." required>
          <input className="input" value={form.name} onChange={set('name')} placeholder="Backend - 2026" required />
        </Field>

        <Field label="Target role" error={errors.target_role}>
          <input className="input" value={form.target_role} onChange={set('target_role')} placeholder="Senior Python roles" />
        </Field>

        <Field label="Notes" error={errors.notes}>
          <textarea className="input min-h-16" value={form.notes} onChange={set('notes')} />
        </Field>

        {isFirst ? (
          <p className="text-xs text-slate-500">Your first resume becomes the default automatically.</p>
        ) : (
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={form.is_default}
              onChange={set('is_default')}
              className="size-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            Make this my default resume
          </label>
        )}
      </form>
    </Modal>
  )
}
