import { Suspense, lazy } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import ProtectedRoute, { PublicOnlyRoute } from './components/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import { PageLoader } from './components/ui'

// Login and Register load eagerly - they are the entry point and must paint
// immediately. Everything behind the auth wall is split, which keeps Recharts
// and the chart pages out of the first-load bundle entirely.
import Login from './pages/Login'
import Register from './pages/Register'
import NotFound from './pages/NotFound'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Jobs = lazy(() => import('./pages/Jobs'))
const AddJob = lazy(() => import('./pages/AddJob'))
const JobDetails = lazy(() => import('./pages/JobDetails'))
const Applications = lazy(() => import('./pages/Applications'))
const Resumes = lazy(() => import('./pages/Resumes'))
const Reminders = lazy(() => import('./pages/Reminders'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Profile = lazy(() => import('./pages/Profile'))
const Settings = lazy(() => import('./pages/Settings'))

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <Routes>
            <Route element={<PublicOnlyRoute />}>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
            </Route>

            <Route element={<ProtectedRoute />}>
              <Route
                element={
                  <Suspense fallback={<PageLoader />}>
                    <AppLayout />
                  </Suspense>
                }
              >
                <Route index element={<Dashboard />} />
                <Route path="jobs" element={<Jobs />} />
                <Route path="jobs/new" element={<AddJob />} />
                <Route path="jobs/:id" element={<JobDetails />} />
                <Route path="jobs/:id/edit" element={<AddJob />} />
                <Route path="applications" element={<Applications />} />
                <Route path="resumes" element={<Resumes />} />
                <Route path="reminders" element={<Reminders />} />
                <Route path="analytics" element={<Analytics />} />
                <Route path="profile" element={<Profile />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Route>

            <Route path="/404" element={<NotFound />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}
