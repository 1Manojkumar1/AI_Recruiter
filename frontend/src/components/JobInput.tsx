import { useCallback } from 'react'
import { FiSearch, FiTrash2, FiZap } from 'react-icons/fi'
import { useCandidateContext } from '../context/CandidateContext'

export default function JobInput() {
  const {
    jobDescription,
    setJobDescription,
    rankCandidatesAction,
    clearResults,
    isLoading,
  } = useCandidateContext()

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        rankCandidatesAction()
      }
    },
    [rankCandidatesAction]
  )

  const handleClear = useCallback(() => {
    setJobDescription('')
    clearResults()
  }, [setJobDescription, clearResults])

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-3">
        <FiSearch className="w-5 h-5 text-primary-500" />
        <h2 className="text-lg font-semibold text-gray-900">Job Description</h2>
      </div>

      <textarea
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Paste job description here...&#10;&#10;Example: Senior Backend Engineer with 5+ years of experience in Python, FastAPI, and Docker. Must have strong system design skills and experience with microservices architecture."
        className="input-field resize-y"
        style={{ minHeight: '100px', maxHeight: '300px' }}
        disabled={isLoading}
      />

      <div className="flex items-center justify-between mt-4">
        <p className="text-xs text-gray-400">
          {jobDescription.length} characters
          {jobDescription.length > 0 && jobDescription.length < 20 && (
            <span className="text-amber-500 ml-2">(min 20 characters)</span>
          )}
        </p>

        <div className="flex items-center gap-3">
          <button
            onClick={handleClear}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            <FiTrash2 className="w-4 h-4" />
            Clear
          </button>

          <button
            onClick={rankCandidatesAction}
            disabled={isLoading || !jobDescription.trim() || jobDescription.trim().length < 20}
            className="btn-primary flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <FiZap className="w-4 h-4" />
                Rank Candidates
              </>
            )}
          </button>
        </div>
      </div>

      <p className="text-xs text-gray-400 mt-2">
        Press Ctrl+Enter to rank quickly
      </p>
    </div>
  )
}
