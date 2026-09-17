import { useState } from 'react'
import { Button, Card, CardHeader, Field } from '../ui'

/** Saved answers to recurring screening questions.
 *
 *  The form filler matches a question on the page against these keys, so a
 *  question answered once is answered on every future application.
 */
export default function CustomAnswers({ value, onChange }) {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')

  const entries = Object.entries(value)

  function add() {
    const key = question.trim()
    if (!key || !answer.trim()) return
    onChange({ ...value, [key]: answer.trim() })
    setQuestion('')
    setAnswer('')
  }

  function remove(key) {
    const next = { ...value }
    delete next[key]
    onChange(next)
  }

  function edit(key, newAnswer) {
    onChange({ ...value, [key]: newAnswer })
  }

  return (
    <Card>
      <CardHeader
        title="Saved answers"
        subtitle="Answers the form filler reuses for questions it has seen before"
      />

      <div className="space-y-4 px-5 py-5">
        {entries.length === 0 ? (
          <p className="text-sm text-slate-500">
            Nothing saved yet. When a run reports a question it could not answer, add it here and the
            next run will fill it.
          </p>
        ) : (
          <ul className="space-y-3">
            {entries.map(([key, savedAnswer]) => (
              <li key={key} className="rounded-lg border border-slate-200 px-3 py-2.5">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-medium text-slate-800">{key}</p>
                  <button
                    type="button"
                    onClick={() => remove(key)}
                    aria-label={`Remove the saved answer for "${key}"`}
                    className="shrink-0 text-xs font-medium text-slate-400 transition hover:text-rose-600"
                  >
                    Remove
                  </button>
                </div>
                <textarea
                  className="input mt-2 min-h-16 text-sm"
                  value={savedAnswer}
                  onChange={(event) => edit(key, event.target.value)}
                  aria-label={`Answer for "${key}"`}
                />
              </li>
            ))}
          </ul>
        )}

        <div className="rounded-lg border border-dashed border-slate-300 px-3 py-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Question">
              <input
                className="input"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Why do you want to work here?"
              />
            </Field>
            <Field label="Your answer">
              <input
                className="input"
                value={answer}
                onChange={(event) => setAnswer(event.target.value)}
                // Enter inside a nested input would submit the whole profile
                // form; intercept it and add the pair instead.
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault()
                    add()
                  }
                }}
              />
            </Field>
          </div>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="mt-2"
            onClick={add}
            disabled={!question.trim() || !answer.trim()}
          >
            Add answer
          </Button>
        </div>
      </div>
    </Card>
  )
}
