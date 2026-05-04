/**
 * Encapsulates the fetch → loading → data/error lifecycle for a
 * single-repo analysis so pages stay clean.
 *
 * Usage:
 *   const { data, loading, error, analyse } = useRepo()
 *   analyse('facebook/react')
 */

import { useState, useCallback } from 'react'
import { getRepo } from '../utils/api'

export default function useRepo() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const analyse = useCallback(async (slug) => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const json = await getRepo(slug)
      setData(json.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const reset = useCallback(() => {
    setData(null)
    setError(null)
  }, [])

  return { data, loading, error, analyse, reset }
}
