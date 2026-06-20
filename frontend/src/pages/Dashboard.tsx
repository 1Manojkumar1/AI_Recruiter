import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiGitBranch } from 'react-icons/fi'
import { useCandidateContext } from '../context/CandidateContext'
import JobInput from '../components/JobInput'
import CandidateCard from '../components/CandidateCard'
import CandidateTable from '../components/CandidateTable'
import CandidateComparison from '../components/CandidateComparison'
import ExplanationCard from '../components/ExplanationCard'
import ScoreBreakdownChart from '../components/ScoreBreakdownChart'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import { formatTime } from '../utils/helpers'
import type { CandidateScore } from '../types'

export default function Dashboard() {
  const navigate = useNavigate()
  const {
    candidates,
    selectedCandidate,
    explanation,
    comparison,
    isLoading,
    isExplaining,
    isComparing,
    error,
    queryTime,
    compareList,
    explainCandidateAction,
    compareCandidatesAction,
    selectCandidate,
    clearError,
    clearCompare,
  } = useCandidateContext()

  const handleViewDetails = useCallback(
    (candidate: CandidateScore) => {
      navigate(`/candidate/${candidate.candidate_id}`)
    },
    [navigate]
  )

  const handleSelectFromTable = useCallback(
    (candidate: CandidateScore) => {
      selectCandidate(candidate)
      explainCandidateAction(candidate.candidate_id)
    },
    [selectCandidate, explainCandidateAction]
  )

  const handleCompare = useCallback(() => {
    if (compareList.length === 2) {
      compareCandidatesAction(compareList[0], compareList[1])
    }
  }, [compareList, compareCandidatesAction])

  return (
    <div className="space-y-6">
      <div className="text-center py-4">
        <h1 className="text-3xl font-bold text-gray-900">AI Candidate Ranking System</h1>
        <p className="mt-2 text-gray-500 max-w-2xl mx-auto">
          Find the best candidates using AI-powered semantic matching and explainable ranking.
        </p>
      </div>

      <JobInput />

      {error && <ErrorMessage message={error} onDismiss={clearError} />}

      {isLoading && (
        <div className="card">
          <LoadingSpinner
            text={
              candidates.length === 0
                ? 'Analyzing Job Description...'
                : 'Calculating Scores...'
            }
            size="lg"
          />
        </div>
      )}

      {isExplaining && !explanation && (
        <div className="card">
          <LoadingSpinner text="Generating Explanation..." size="sm" />
        </div>
      )}

      {isComparing && (
        <div className="card">
          <LoadingSpinner text="Comparing Candidates..." size="sm" />
        </div>
      )}

      {!isLoading && candidates.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Results
                {queryTime > 0 && (
                  <span className="ml-2 text-sm font-normal text-gray-400">
                    ({formatTime(queryTime)})
                  </span>
                )}
              </h2>
              <p className="text-sm text-gray-500">
                {candidates.length} candidates ranked
              </p>
            </div>

            {compareList.length === 2 && (
              <button
                onClick={handleCompare}
                disabled={isComparing}
                className="btn-primary flex items-center gap-2"
              >
                <FiGitBranch className="w-4 h-4" />
                Compare Selected ({compareList.length})
              </button>
            )}

            {compareList.length === 1 && (
              <p className="text-xs text-gray-500">
                Select 1 more candidate to compare
              </p>
            )}
          </div>

          <CandidateComparison
            candidates={candidates}
            comparison={comparison}
            onClose={clearCompare}
          />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {candidates.slice(0, 6).map((c) => (
                  <CandidateCard
                    key={c.candidate_id}
                    candidate={c}
                    onViewDetails={handleViewDetails}
                  />
                ))}
              </div>

              <CandidateTable candidates={candidates} onSelect={handleSelectFromTable} />
            </div>

            <div className="space-y-6">
              {selectedCandidate && (
                <>
                  <ScoreBreakdownChart candidate={selectedCandidate} />
                  {explanation && (
                    <ExplanationCard
                      explanation={explanation}
                      rank={selectedCandidate.rank}
                      candidateName={selectedCandidate.candidate_id}
                    />
                  )}
                </>
              )}

              {!selectedCandidate && candidates.length > 0 && (
                <div className="card text-center py-12">
                  <p className="text-sm text-gray-400">
                    Select a candidate to view score breakdown and explanation
                  </p>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {!isLoading && candidates.length === 0 && !error && (
        <div className="card text-center py-16">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FiGitBranch className="w-8 h-8 text-primary-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Rank</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            Paste a job description above and click "Rank Candidates" to find the best matches
            from our database of candidates.
          </p>
        </div>
      )}
    </div>
  )
}
