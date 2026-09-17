import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { auth } from '../api/endpoints'
import client, { setAuthFailureHandler, tokenStore } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // Distinct from "no user": on a hard refresh we hold a token but do not yet
  // know if it is valid, and routing must wait rather than bounce to /login.
  const [initialising, setInitialising] = useState(true)

  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
  }, [])

  useEffect(() => {
    setAuthFailureHandler(logout)
  }, [logout])

  useEffect(() => {
    if (!tokenStore.access) {
      setInitialising(false)
      return
    }
    auth
      .me()
      .then((response) => setUser(response.data))
      .catch(() => tokenStore.clear())
      .finally(() => setInitialising(false))
  }, [])

  const login = useCallback(async (credentials) => {
    const { data } = await auth.login(credentials)
    tokenStore.set(data)
    setUser(data.user)
    return data.user
  }, [])

  const register = useCallback(async (payload) => {
    const { data } = await auth.register(payload)
    tokenStore.set(data)
    setUser(data.user)
    return data.user
  }, [])

  const refreshUser = useCallback(async () => {
    const { data } = await auth.me()
    setUser(data)
    return data
  }, [])

  const value = useMemo(
    () => ({ user, initialising, login, register, logout, refreshUser, isAuthenticated: !!user }),
    [user, initialising, login, register, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside an AuthProvider')
  return context
}

export { client }
