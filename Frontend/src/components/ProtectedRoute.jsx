import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { PageLoader } from './ui'

/** Blocks render until the stored token has been validated, so a hard refresh
 *  on a deep link does not flash the login page before landing. */
export default function ProtectedRoute() {
  const { isAuthenticated, initialising } = useAuth()
  const location = useLocation()

  if (initialising) return <PageLoader label="Signing you in" />
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}

export function PublicOnlyRoute() {
  const { isAuthenticated, initialising } = useAuth()
  if (initialising) return <PageLoader />
  if (isAuthenticated) return <Navigate to="/" replace />
  return <Outlet />
}
