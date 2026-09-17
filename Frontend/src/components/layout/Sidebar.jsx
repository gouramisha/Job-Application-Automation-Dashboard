import { NavLink } from 'react-router-dom'

const NAV_SECTIONS = [
  {
    heading: 'Overview',
    items: [
      { to: '/', label: 'Dashboard', icon: '▦', end: true },
      { to: '/analytics', label: 'Analytics', icon: '◔' },
    ],
  },
  {
    heading: 'Pipeline',
    items: [
      { to: '/jobs', label: 'Jobs', icon: '▤' },
      { to: '/applications', label: 'Applications', icon: '✈' },
      { to: '/reminders', label: 'Reminders', icon: '◷' },
    ],
  },
  {
    heading: 'Your details',
    items: [
      { to: '/resumes', label: 'Resumes', icon: '▣' },
      { to: '/profile', label: 'Profile', icon: '☺' },
      { to: '/settings', label: 'Settings', icon: '⚙' },
    ],
  },
]

export default function Sidebar({ open, onNavigate }) {
  return (
    <>
      {/* Scrim only exists on mobile, where the sidebar overlays content. */}
      {open && (
        <button
          type="button"
          aria-label="Close menu"
          onClick={onNavigate}
          className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-800 bg-slate-900
          transition-transform duration-200 lg:translate-x-0
          ${open ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex h-16 shrink-0 items-center gap-2.5 border-b border-slate-800 px-5">
          <span className="flex size-8 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
            J
          </span>
          <span className="text-base font-semibold text-white">JobTrack</span>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
          {NAV_SECTIONS.map((section) => (
            <div key={section.heading}>
              <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                {section.heading}
              </p>
              <ul className="space-y-0.5">
                {section.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.end}
                      onClick={onNavigate}
                      className={({ isActive }) =>
                        `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                          isActive
                            ? 'bg-brand-600 text-white'
                            : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                        }`
                      }
                    >
                      <span aria-hidden="true" className="w-4 text-center">{item.icon}</span>
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        <div className="shrink-0 border-t border-slate-800 p-4">
          <p className="text-[11px] leading-relaxed text-slate-500">
            Automation fills forms for you and stops before Submit, unless a site
            offers an official application API.
          </p>
        </div>
      </aside>
    </>
  )
}
