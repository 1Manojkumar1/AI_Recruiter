import { useState, useMemo, useCallback, memo } from 'react'
import { FiArrowUp, FiArrowDown, FiSearch } from 'react-icons/fi'
import { formatScore, getScoreColor } from '../utils/helpers'
import type { CandidateScore } from '../types'

type SortField = 'rank' | 'final_score' | 'skill_score' | 'experience_score' | 'education_score' | 'semantic_score' | 'achievement_score'
type SortDir = 'asc' | 'desc'

interface CandidateTableProps {
  candidates: CandidateScore[]
  onSelect: (candidate: CandidateScore) => void
}

const columns: { key: SortField; label: string }[] = [
  { key: 'rank', label: 'Rank' },
  { key: 'final_score', label: 'Final' },
  { key: 'semantic_score', label: 'Semantic' },
  { key: 'skill_score', label: 'Skill' },
  { key: 'experience_score', label: 'Experience' },
  { key: 'education_score', label: 'Education' },
  { key: 'achievement_score', label: 'Achievement' },
]

function CandidateTable({ candidates, onSelect }: CandidateTableProps) {
  const [sortField, setSortField] = useState<SortField>('rank')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [search, setSearch] = useState('')

  const handleSort = useCallback((field: SortField) => {
    setSortField((prev) => {
      if (prev === field) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
        return field
      }
      setSortDir('desc')
      return field
    })
  }, [])

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    let list = candidates
    if (q) {
      list = candidates.filter(
        (c) =>
          c.candidate_id.toLowerCase().includes(q) ||
          c.profile_summary.toLowerCase().includes(q)
      )
    }
    return [...list].sort((a, b) => {
      const aVal = a[sortField]
      const bVal = b[sortField]
      const mult = sortDir === 'asc' ? 1 : -1
      return (aVal - bVal) * mult
    })
  }, [candidates, sortField, sortDir, search])

  if (candidates.length === 0) return null

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">
          Ranked Candidates ({filtered.length})
        </h3>
        <div className="relative">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID or profile..."
            className="pl-9 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none w-56"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className="px-3 py-2.5 text-left font-medium text-gray-500 cursor-pointer hover:text-gray-700 select-none whitespace-nowrap"
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {sortField === col.key ? (
                      sortDir === 'asc' ? (
                        <FiArrowUp className="w-3 h-3 text-primary-500" />
                      ) : (
                        <FiArrowDown className="w-3 h-3 text-primary-500" />
                      )
                    ) : null}
                  </div>
                </th>
              ))}
              <th className="px-3 py-2.5 text-left font-medium text-gray-500 whitespace-nowrap">
                ID
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr
                key={c.candidate_id}
                onClick={() => onSelect(c)}
                className="border-b border-gray-50 hover:bg-primary-50/50 cursor-pointer transition-colors"
              >
                <td className="px-3 py-2.5 font-medium text-gray-900">#{c.rank}</td>
                <td className={`px-3 py-2.5 font-bold ${getScoreColor(c.final_score)}`}>
                  {formatScore(c.final_score)}
                </td>
                <td className="px-3 py-2.5 text-gray-600">{formatScore(c.semantic_score)}</td>
                <td className="px-3 py-2.5 text-gray-600">{formatScore(c.skill_score)}</td>
                <td className="px-3 py-2.5 text-gray-600">{formatScore(c.experience_score)}</td>
                <td className="px-3 py-2.5 text-gray-600">{formatScore(c.education_score)}</td>
                <td className="px-3 py-2.5 text-gray-600">{formatScore(c.achievement_score)}</td>
                <td className="px-3 py-2.5 text-gray-500 font-mono">{c.candidate_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && search && (
        <div className="text-center py-6 text-sm text-gray-400">
          No candidates match "{search}"
        </div>
      )}
    </div>
  )
}

export default memo(CandidateTable)
