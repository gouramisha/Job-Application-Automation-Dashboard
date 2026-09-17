import axios from 'axios'

const TOKEN_KEY = 'jobtrack.access'
const REFRESH_KEY = 'jobtrack.refresh'

export const tokenStore = {
  get access() {
    return localStorage.getItem(TOKEN_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  set({ access, refresh }) {
    if (access) localStorage.setItem(TOKEN_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = tokenStore.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  // Let the browser set the multipart boundary itself.
  if (config.data instanceof FormData) delete config.headers['Content-Type']
  return config
})

// A burst of parallel requests can all 401 at once on an expired access
// token. Without this, each would fire its own refresh and the rotating
// refresh token would invalidate the others. Instead the first refresh wins
// and everyone else waits on the same promise.
let refreshPromise = null
let onAuthFailure = () => {}

export function setAuthFailureHandler(handler) {
  onAuthFailure = handler
}

async function refreshAccessToken() {
  const refresh = tokenStore.refresh
  if (!refresh) throw new Error('No refresh token')

  refreshPromise =
    refreshPromise ||
    axios
      .post(`${client.defaults.baseURL}/auth/refresh/`, { refresh })
      .then((response) => {
        tokenStore.set(response.data)
        return response.data.access
      })
      .finally(() => {
        refreshPromise = null
      })

  return refreshPromise
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status
    const isAuthCall = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh')

    if (status === 401 && original && !original._retried && !isAuthCall) {
      original._retried = true
      try {
        const access = await refreshAccessToken()
        original.headers.Authorization = `Bearer ${access}`
        return client(original)
      } catch {
        tokenStore.clear()
        onAuthFailure()
      }
    }
    return Promise.reject(error)
  },
)

/** Flatten DRF's error shapes into one readable line for a toast. */
export function apiErrorMessage(error, fallback = 'Something went wrong.') {
  const data = error?.response?.data
  if (!data) return error?.message || fallback
  if (typeof data === 'string') return data
  if (data.detail) return data.detail

  const first = Object.entries(data)[0]
  if (!first) return fallback
  const [field, value] = first
  const text = Array.isArray(value) ? value[0] : value
  return field === 'non_field_errors' ? text : `${field}: ${text}`
}

export default client
