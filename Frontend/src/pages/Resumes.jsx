import { useState } from 'react'
import { resumes as resumesApi } from '../api/endpoints'
import { useApi } from '../hooks/useApi'
import { apiErrorMessage } from '../api/client'
import { useToast } from '../context/ToastContext'
import { Badge, Button, Card, EmptyState, PageLoader } from '../components/ui'
import UploadResumeModal from '../components/resumes/UploadResumeModal'
import { formatBytes, formatDate } from '../lib/format'

export default function Resumes() {
  const [uploadOpen, setUploadOpen] = useState(false)
  const toast = useToast()
  const { data, loading, error, reload } = useApi(() => resumesApi.list(), [])

  async function setDefault(resume) {
    try {
      await resumesApi.setDefault(resume.id)
      toast.success(`"${resume.name}" is now your default resume.`)
      reload()
    } catch (caught) {
      toast.error(apiErrorMessage(caught))
    }
  }

  async function remove(resume) {
    if (!window.confirm(`Delete "${resume.name}"? The file is removed permanently.`)) return
    try {
      await resumesApi.remove(resume.id)
      toast.success('Resume deleted.')
      reload()
    } catch (caught) {
      toast.error(apiErrorMessage(caught))
    }
  }

  const rows = data?.results ?? []

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-500">
          Keep a version per role. The default is attached automatically when you apply.
        </p>
        <Button onClick={() => setUploadOpen(true)}>+ Upload resume</Button>
      </div>

      {error ? (
        <Card>
          <EmptyState icon="⚠" title="Could not load your resumes" description={error}
            action={<Button onClick={reload}>Try again</Button>} />
        </Card>
      ) : loading && !data ? (
        <PageLoader label="Loading resumes" />
      ) : rows.length === 0 ? (
        <Card>
          <EmptyState
            icon="📄"
            title="No resumes yet"
            description="Upload at least one. Assisted form filling attaches it for you, and each application records which version went out."
            action={<Button onClick={() => setUploadOpen(true)}>Upload your first resume</Button>}
          />
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((resume) => (
            <Card key={resume.id} className="flex flex-col px-5 py-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="truncate font-medium text-slate-900">{resume.name}</h3>
                  {resume.target_role && (
                    <p className="mt-0.5 truncate text-xs text-slate-500">For {resume.target_role}</p>
                  )}
                </div>
                {resume.is_default && (
                  <Badge className="shrink-0 bg-emerald-50 text-emerald-700 ring-emerald-200">Default</Badge>
                )}
              </div>

              <p className="mt-3 truncate text-xs text-slate-400">
                {resume.filename} · {formatBytes(resume.size_bytes)}
              </p>
              <p className="text-xs text-slate-400">Added {formatDate(resume.created_at)}</p>

              {resume.notes && <p className="mt-2 line-clamp-2 text-xs text-slate-500">{resume.notes}</p>}

              <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
                <a href={resume.file_url} target="_blank" rel="noopener noreferrer">
                  <Button size="sm" variant="secondary">View</Button>
                </a>
                {!resume.is_default && (
                  <Button size="sm" variant="ghost" onClick={() => setDefault(resume)}>Make default</Button>
                )}
                <button
                  type="button"
                  onClick={() => remove(resume)}
                  className="ml-auto text-xs font-medium text-slate-400 transition hover:text-rose-600"
                >
                  Delete
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <UploadResumeModal
        open={uploadOpen}
        isFirst={rows.length === 0}
        onClose={() => setUploadOpen(false)}
        onDone={() => { setUploadOpen(false); reload() }}
      />
    </div>
  )
}
