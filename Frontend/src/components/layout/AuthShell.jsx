/** Split layout shared by Login and Register: form on the left, a short
 *  product pitch on the right that collapses away on small screens. */
export default function AuthShell({ title, subtitle, children, footer }) {
  const highlights = [
    ['Track every application', 'Six statuses from Saved to Selected, with a full history of each move.'],
    ['Never miss a follow-up', 'Reminders schedule themselves the moment you record an application.'],
    ['See what is working', 'Conversion rates, funnels and trends across your whole search.'],
    ['Fill forms faster', 'Automation types the repetitive fields. You review and press Submit.'],
  ]

  return (
    <div className="flex min-h-screen bg-white">
      <div className="flex w-full flex-col justify-center px-6 py-12 lg:w-1/2 lg:px-16">
        <div className="mx-auto w-full max-w-sm">
          <div className="mb-8 flex items-center gap-2.5">
            <span className="flex size-9 items-center justify-center rounded-lg bg-brand-600 text-base font-bold text-white">
              J
            </span>
            <span className="text-lg font-semibold text-slate-900">JobTrack</span>
          </div>

          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
          {subtitle && <p className="mt-2 text-sm text-slate-500">{subtitle}</p>}

          <div className="mt-8">{children}</div>
          {footer && <div className="mt-6 text-center text-sm text-slate-500">{footer}</div>}
        </div>
      </div>

      <div className="hidden bg-slate-900 lg:flex lg:w-1/2 lg:flex-col lg:justify-center lg:px-16">
        <h2 className="text-2xl font-bold text-white">
          Run your job search like a pipeline.
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-400">
          Stop guessing which applications are stalling. Track, follow up and measure.
        </p>
        <ul className="mt-10 space-y-6">
          {highlights.map(([heading, description]) => (
            <li key={heading} className="flex gap-4">
              <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-600 text-xs text-white">
                ✓
              </span>
              <div>
                <p className="text-sm font-semibold text-white">{heading}</p>
                <p className="mt-0.5 text-sm leading-relaxed text-slate-400">{description}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
