import { useState, useEffect, useCallback } from 'react'
import { getCandidate, getHealth } from '../services/api'
import type { CandidateDetail, HealthResponse } from '../types'

export function useCandidateDetail(candidateId: string | undefined) {
  const [candidate, setCandidate] = useState<CandidateDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!candidateId) {
      setLoading(false)
      return
    }

    let cancelled = false

    async function fetchCandidate() {
      setLoading(true)
      setError(null)
      try {
        const data = await getCandidate(candidateId!)
        if (!cancelled) {
          setCandidate(data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load candidate')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchCandidate()
    return () => { cancelled = true }
  }, [candidateId])

  return { candidate, loading, error }
}

export function useHealthCheck() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const checkHealth = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getHealth()
      setHealth(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Health check failed')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  return { health, loading, error, refetch: checkHealth }
}
