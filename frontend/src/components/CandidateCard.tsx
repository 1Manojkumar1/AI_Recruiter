import { memo, useCallback } from 'react'
import { FiUser, FiStar, FiEye, FiGitBranch, FiChevronRight } from 'react-icons/fi'
import { useCandidateContext } from '../context/CandidateContext'
import { getScoreColor, getScoreBadgeColor, getScoreLabel, formatScore, getSeniorityColor } from '../utils/helpers'
import type { CandidateScore } from '../types'

interface CandidateCardProps {
  candidate: CandidateScore
  onViewDetails: (candidate: CandidateScore) => void
}

function CandidateCard({ candidate, onViewDetails }: CandidateCardProps) {
  const { toggleCompare, compareList } = useCandidateContext()
  const isSelected = compareList.includes(candidate.candidate_id)

  const handleCompare = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation()
      toggleCompare(candidate.candidate_id)
    },
    [candidate.candidate_id, toggleCompare]
  )

  const handleView = useCallback(() => {
    onViewDetails(candidate)
  }, [candidate, onViewDetails])

  return (
    <div
      className={`card hover:shadow-md transition-all duration-200 cursor-pointer group ${
        isSelected ? 'ring-2 ring-primary-500 border-primary-200' : ''
      }`}
      onClick={handleView}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full flex items-center justify-center flex-shrink-0">
            <FiUser className="w-5 h-5 text-primary-600" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-semibold text-gray-900 truncate">
                {candidate.candidate_id}
              </h3>
              {candidate.seniority && (
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getSeniorityColor(candidate.seniority)}`}>
                  {candidate.seniority}
                </span>
              )}
            </div>

            {candidate.profile_summary && (
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                {candidate.profile_summary}
              </p>
            )}

            <div className="flex items-center gap-3 mt-2 flex-wrap">
              {candidate.total_experience_years > 0 && (
                <span className="text-xs text-gray-500">
                  {candidate.total_experience_years}y exp
                </span>
              )}
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getScoreBadgeColor(candidate.final_score)}`}>
                {getScoreLabel(candidate.final_score)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 ml-3">
          <div className="text-right">
            <div className={`text-2xl font-bold ${getScoreColor(candidate.final_score)}`}>
              {formatScore(candidate.final_score)}
            </div>
            <div className="text-xs text-gray-400">/ 100</div>
          </div>

          <FiChevronRight className="w-4 h-4 text-gray-300 group-hover:text-primary-500 transition-colors" />
        </div>
      </div>

      {candidate.strengths && candidate.strengths.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex items-center gap-1 mb-1.5">
            <FiStar className="w-3 h-3 text-amber-500" />
            <span className="text-xs font-medium text-gray-600">Strengths</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {candidate.strengths.slice(0, 3).map((s, i) => (
              <span key={i} className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">
                {s}
              </span>
            ))}
            {candidate.strengths.length > 3 && (
              <span className="text-xs text-gray-400">+{candidate.strengths.length - 3} more</span>
            )}
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100">
        <button
          onClick={handleView}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium text-primary-600 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
        >
          <FiEye className="w-3 h-3" />
          View Details
        </button>

        <button
          onClick={handleCompare}
          className={`flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
            isSelected
              ? 'text-primary-700 bg-primary-100'
              : 'text-gray-600 bg-gray-100 hover:bg-gray-200'
          }`}
        >
          <FiGitBranch className="w-3 h-3" />
          {isSelected ? 'Selected' : 'Compare'}
        </button>
      </div>
    </div>
  )
}

export default memo(CandidateCard)
