import { memo } from 'react'
import { FiCheckCircle, FiAlertTriangle, FiFileText, FiThumbsUp } from 'react-icons/fi'
import type { ExplanationResponse } from '../types'

interface ExplanationCardProps {
  explanation: ExplanationResponse
  candidateName?: string
  rank?: number
}

function ExplanationCard({ explanation, candidateName, rank }: ExplanationCardProps) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
          <FiFileText className="w-4 h-4 text-primary-600" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-900">
            Why ranked {rank ? `#${rank}` : 'here'}
          </h3>
          {candidateName && (
            <p className="text-xs text-gray-500">{candidateName}</p>
          )}
        </div>
      </div>

      {explanation.strengths.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-1.5 mb-2">
            <FiCheckCircle className="w-4 h-4 text-emerald-500" />
            <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">Strengths</span>
          </div>
          <ul className="space-y-1.5">
            {explanation.strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="text-emerald-500 mt-0.5">&#10003;</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {explanation.weaknesses.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-1.5 mb-2">
            <FiAlertTriangle className="w-4 h-4 text-amber-500" />
            <span className="text-xs font-semibold text-amber-700 uppercase tracking-wide">Areas for Growth</span>
          </div>
          <ul className="space-y-1.5">
            {explanation.weaknesses.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="text-amber-500 mt-0.5">&#9888;</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {explanation.summary && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-700 leading-relaxed">{explanation.summary}</p>
        </div>
      )}

      {explanation.recommendation && (
        <div className="flex items-start gap-2 p-3 bg-primary-50 rounded-lg">
          <FiThumbsUp className="w-4 h-4 text-primary-500 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-primary-800 font-medium">{explanation.recommendation}</p>
        </div>
      )}
    </div>
  )
}

export default memo(ExplanationCard)
