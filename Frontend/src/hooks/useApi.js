import { useCallback, useEffect, useRef, useState } from 'react'
import { apiErrorMessage } from '../api/client'

/** Fetch-on-mount with a manual `reload`. `deps` behaves like useEffect's. */
export function useApi(fetcher, deps = [], { immediate = true } = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState(null)

  // Guards against setting state after unmount, and against an earlier slow
  // request overwriting a later fast one.
  const requestId = useRef(0)
  const mounted = useRef(true)
  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  const run = useCallback(async () => {
    const id = ++requestId.current
    setLoading(true)
    setError(null)
    try {
      const response = await fetcher()
      if (mounted.current && id === requestId.current) setData(response.data)
      return response.data
    } catch (caught) {
      if (mounted.current && id === requestId.current) setError(apiErrorMessage(caught))
      throw caught
    } finally {
      if (mounted.current && id === requestId.current) setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    if (immediate) run().catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run, immediate])

  return { data, loading, error, reload: run, setData }
}

/** Delays a rapidly changing value - used for search-as-you-type. */
export function useDebounced(value, delay = 350) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}
