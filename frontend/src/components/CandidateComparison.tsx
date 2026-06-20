import { memo } from 'react'
import { FiX, FiArrowRight } from 'react-icons/fi'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
  ResponsiveContainer,
} from 'recharts'
import { useCandidateContext } from '../context/CandidateContext'
import { formatScore, getScoreColor } from '../utils/helpers'
import type { CandidateScore, ComparisonResponse } from '../types'

interface CandidateComparisonProps {
  candidates: CandidateScore[]
  comparison: ComparisonResponse | null
  onClose: () => void
}

function CandidateComparison({ candidates, comparison, onClose }: CandidateComparisonProps) {
  const { compareList, clearCompare } = useCandidateContext()

  if (compareList.length < 2) return null

  const candA = candidates.find((c) => c.candidate_id === compareList[0])
  const candB = candidates.find((c) => c.candidate_id === compareList[1])

  if (!candA || !candB) return null

  const radarData = [
    { subject: 'Semantic', A: candA.semantic_score, B: candB.semantic_score },
    { subject: 'Skills', A: candA.skill_score, B: candB.skill_score },
    { subject: 'Experience', A: candA.experience_score, B: candB.experience_score },
    { subject: 'Education', A: candA.education_score, B: candB.education_score },
    { subject: 'Achievement', A: candA.achievement_score, B: candB.achievement_score },
  ]

  return (
    <div className="card border-2 border-primary-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">Candidate Comparison</h3>
        <button
          onClick={() => { clearCompare(); onClose(); }}
          className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
        >
          <FiX className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-blue-50 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-blue-700">Candidate A</span>
          </div>
          <p className="text-sm font-medium text-gray-900">{candA.candidate_id}</p>
          <p className={`text-2xl font-bold mt-1 ${getScoreColor(candA.final_score)}`}>
            {formatScore(candA.final_score)}
          </p>
        </div>

        <div className="p-3 bg-emerald-50 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-emerald-700">Candidate B</span>
          </div>
          <p className="text-sm font-medium text-gray-900">{candB.candidate_id}</p>
          <p className={`text-2xl font-bold mt-1 ${getScoreColor(candB.final_score)}`}>
            {formatScore(candB.final_score)}
          </p>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        {['semantic_score', 'skill_score', 'experience_score', 'education_score', 'achievement_score'].map((key) => {
          const label = key.replace('_score', '').replace('_', ' ')
          const aVal = candA[key as keyof CandidateScore] as number
          const bVal = candB[key as keyof CandidateScore] as number
          const maxVal = Math.max(aVal, bVal, 1)

          return (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs text-gray-500 w-20 capitalize">{label}</span>
              <div className="flex-1 flex items-center gap-2">
                <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${(aVal / maxVal) * 100}%` }}
                  />
                </div>
                <span className="text-xs font-medium text-gray-700 w-8 text-right">{aVal.toFixed(0)}</span>
                <FiArrowRight className="w-3 h-3 text-gray-300" />
                <span className="text-xs font-medium text-gray-700 w-8">{bVal.toFixed(0)}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full"
                    style={{ width: `${(bVal / maxVal) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="h-56 mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#6b7280' }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9, fill: '#9ca3af' }} />
            <Radar name="Candidate A" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} strokeWidth={2} />
            <Radar name="Candidate B" dataKey="B" stroke="#10b981" fill="#10b981" fillOpacity={0.2} strokeWidth={2} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {comparison && (
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-xs font-semibold text-gray-700 mb-2">AI Analysis</p>
          {comparison.candidate_A_advantage.length > 0 && (
            <div className="mb-2">
              <p className="text-xs text-blue-600 font-medium mb-1">{comparison.candidate_A_id} advantages:</p>
              <ul className="space-y-0.5">
                {comparison.candidate_A_advantage.map((a, i) => (
                  <li key={i} className="text-xs text-gray-600 flex items-start gap-1">
                    <span className="text-blue-500">+</span> {a}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {comparison.candidate_B_advantage.length > 0 && (
            <div className="mb-2">
              <p className="text-xs text-emerald-600 font-medium mb-1">{comparison.candidate_B_id} advantages:</p>
              <ul className="space-y-0.5">
                {comparison.candidate_B_advantage.map((a, i) => (
                  <li key={i} className="text-xs text-gray-600 flex items-start gap-1">
                    <span className="text-emerald-500">+</span> {a}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {comparison.final_reason && (
            <p className="text-xs text-gray-700 mt-2 pt-2 border-t border-gray-200 font-medium">
              {comparison.final_reason}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default memo(CandidateComparison)
