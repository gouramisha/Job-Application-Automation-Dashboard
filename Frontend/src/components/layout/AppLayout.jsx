import { useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useAuth } from '../../context/AuthContext'
import { initials } from '../../lib/format'
import { Button } from '../ui'

const TITLES = {
  '/': 'Dashboard',
  '/jobs': 'Jobs',
  '/jobs/new': 'Add job',
  '/applications': 'Applications',
  '/resumes': 'Resumes',
  '/reminders': 'Reminders',
  '/analytics': 'Analytics',
  '/profile': 'Profile',
  '/settings': 'Settings',
}

export default function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const { user, logout } = useAuth()
  const { pathname } = useLocation()

  const title = TITLES[pathname] || (pathname.startsWith('/jobs/') ? 'Job details' : 'JobTrack')

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar open={menuOpen} onNavigate={() => setMenuOpen(false)} />

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b border-slate-200 bg-white/90 px-4 backdrop-blur sm:px-6">
          <button
            type="button"
            aria-label="Open menu"
            onClick={() => setMenuOpen(true)}
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 lg:hidden"
          >
            ☰
          </button>

          <h1 className="flex-1 truncate text-lg font-semibold text-slate-900">{title}</h1>

          <Link to="/jobs/new" className="hidden sm:block">
            <Button size="sm">+ Add job</Button>
          </Link>

          <div className="relative">
            <button
              type="button"
              onClick={() => setUserMenuOpen((open) => !open)}
              aria-haspopup="menu"
              aria-expanded={userMenuOpen}
              className="flex size-9 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700 transition hover:bg-brand-200"
            >
              {initials(user?.full_name || user?.email)}
            </button>

            {userMenuOpen && (
              <>
                <button
                  type="button"
                  aria-label="Close user menu"
                  className="fixed inset-0 z-10 cursor-default"
                  onClick={() => setUserMenuOpen(false)}
                />
                <div className="absolute right-0 z-20 mt-2 w-56 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
                  <div className="border-b border-slate-100 px-4 py-3">
                    <p className="truncate text-sm font-medium text-slate-900">{user?.full_name}</p>
                    <p className="truncate text-xs text-slate-500">{user?.email}</p>
                  </div>
                  <Link
                    to="/profile"
                    onClick={() => setUserMenuOpen(false)}
                    className="block px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50"
                  >
                    Your profile
                  </Link>
                  <Link
                    to="/settings"
                    onClick={() => setUserMenuOpen(false)}
                    className="block px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-50"
                  >
                    Settings
                  </Link>
                  <button
                    type="button"
                    onClick={logout}
                    className="block w-full border-t border-slate-100 px-4 py-2 text-left text-sm text-rose-600 transition hover:bg-rose-50"
                  >
                    Sign out
                  </button>
                </div>
              </>
            )}
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
