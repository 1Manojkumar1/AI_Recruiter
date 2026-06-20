import React, { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import type { CandidateScore, ExplanationResponse, ComparisonResponse, RankResponse } from '../types'
import { rankCandidates as apiRank, explainCandidate as apiExplain, compareCandidates as apiCompare } from '../services/api'

interface CandidateContextType {
  candidates: CandidateScore[]
  selectedCandidate: CandidateScore | null
  explanation: ExplanationResponse | null
  comparison: ComparisonResponse | null
  jobDescription: string
  isLoading: boolean
  isExplaining: boolean
  isComparing: boolean
  error: string | null
  queryTime: number
  weightsUsed: Record<string, number>
  compareList: string[]
  setJobDescription: (jd: string) => void
  rankCandidatesAction: () => Promise<void>
  explainCandidateAction: (candidateId: string) => Promise<void>
  compareCandidatesAction: (candidateAId: string, candidateBId: string) => Promise<void>
  selectCandidate: (candidate: CandidateScore | null) => void
  clearResults: () => void
  clearError: () => void
  toggleCompare: (candidateId: string) => void
  clearCompare: () => void
}

const CandidateContext = createContext<CandidateContextType | undefined>(undefined)

export function CandidateProvider({ children }: { children: ReactNode }) {
  const [candidates, setCandidates] = useState<CandidateScore[]>([])
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateScore | null>(null)
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null)
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [topN] = useState(100)
  const [isLoading, setIsLoading] = useState(false)
  const [isExplaining, setIsExplaining] = useState(false)
  const [isComparing, setIsComparing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [queryTime, setQueryTime] = useState(0)
  const [weightsUsed, setWeightsUsed] = useState<Record<string, number>>({})
  const [compareList, setCompareList] = useState<string[]>([])

  const rankCandidatesAction = useCallback(async () => {
    if (!jobDescription.trim()) {
      setError('Please enter a job description')
      return
    }
    if (jobDescription.trim().length < 20) {
      setError('Job description must be at least 20 characters')
      return
    }

    setIsLoading(true)
    setError(null)
    setExplanation(null)
    setComparison(null)

    try {
      const result: RankResponse = await apiRank(jobDescription, topN)
      setCandidates(result.candidates)
      setQueryTime(result.query_time_ms)
      setWeightsUsed(result.weights_used)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rank candidates')
    } finally {
      setIsLoading(false)
    }
  }, [jobDescription, topN])

  const explainCandidateAction = useCallback(async (candidateId: string) => {
    setIsExplaining(true)
    setError(null)

    try {
      const result = await apiExplain(candidateId, jobDescription)
      setExplanation(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate explanation')
    } finally {
      setIsExplaining(false)
    }
  }, [jobDescription])

  const compareCandidatesAction = useCallback(async (candidateAId: string, candidateBId: string) => {
    setIsComparing(true)
    setError(null)

    try {
      const result = await apiCompare(candidateAId, candidateBId, jobDescription)
      setComparison(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare candidates')
    } finally {
      setIsComparing(false)
    }
  }, [jobDescription])

  const selectCandidate = useCallback((candidate: CandidateScore | null) => {
    setSelectedCandidate(candidate)
    setExplanation(null)
  }, [])

  const clearResults = useCallback(() => {
    setCandidates([])
    setSelectedCandidate(null)
    setExplanation(null)
    setComparison(null)
    setError(null)
    setQueryTime(0)
    setWeightsUsed({})
    setCompareList([])
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const toggleCompare = useCallback((candidateId: string) => {
    setCompareList((prev) => {
      if (prev.includes(candidateId)) {
        return prev.filter((id) => id !== candidateId)
      }
      if (prev.length >= 2) {
        return [prev[1], candidateId]
      }
      return [...prev, candidateId]
    })
  }, [])

  const clearCompare = useCallback(() => {
    setCompareList([])
    setComparison(null)
  }, [])

  return (
    <CandidateContext.Provider
      value={{
        candidates,
        selectedCandidate,
        explanation,
        comparison,
        jobDescription,
        isLoading,
        isExplaining,
        isComparing,
        error,
        queryTime,
        weightsUsed,
        compareList,
        setJobDescription,
        rankCandidatesAction,
        explainCandidateAction,
        compareCandidatesAction,
        selectCandidate,
        clearResults,
        clearError,
        toggleCompare,
        clearCompare,
      }}
    >
      {children}
    </CandidateContext.Provider>
  )
}

export function useCandidateContext(): CandidateContextType {
  const context = useContext(CandidateContext)
  if (!context) {
    throw new Error('useCandidateContext must be used within a CandidateProvider')
  }
  return context
}
