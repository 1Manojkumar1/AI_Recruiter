import { memo, useState } from 'react'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { FiBarChart2, FiPieChart, FiActivity } from 'react-icons/fi'
import type { CandidateScore } from '../types'

interface ScoreBreakdownChartProps {
  candidate: CandidateScore
}

type ChartType = 'radar' | 'bar' | 'pie'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4']

function ScoreBreakdownChart({ candidate }: ScoreBreakdownChartProps) {
  const [chartType, setChartType] = useState<ChartType>('radar')

  const data = [
    { subject: 'Semantic', value: candidate.semantic_score, fullMark: 100 },
    { subject: 'Skills', value: candidate.skill_score, fullMark: 100 },
    { subject: 'Experience', value: candidate.experience_score, fullMark: 100 },
    { subject: 'Education', value: candidate.education_score, fullMark: 100 },
    { subject: 'Achievement', value: candidate.achievement_score, fullMark: 100 },
  ]

  const barData = data.map((d) => ({ name: d.subject, score: d.value }))
  const pieData = data.map((d) => ({ name: d.subject, value: d.value }))

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">Score Breakdown</h3>
        <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
          <button
            onClick={() => setChartType('radar')}
            className={`p-1.5 rounded-md transition-colors ${
              chartType === 'radar' ? 'bg-white shadow-sm text-primary-600' : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            <FiActivity className="w-4 h-4" />
          </button>
          <button
            onClick={() => setChartType('bar')}
            className={`p-1.5 rounded-md transition-colors ${
              chartType === 'bar' ? 'bg-white shadow-sm text-primary-600' : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            <FiBarChart2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => setChartType('pie')}
            className={`p-1.5 rounded-md transition-colors ${
              chartType === 'pie' ? 'bg-white shadow-sm text-primary-600' : 'text-gray-400 hover:text-gray-600'
            }`}
          >
            <FiPieChart className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="h-64">
        {chartType === 'radar' && (
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={data}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: '#6b7280' }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <Radar
                name="Score"
                dataKey="value"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
        )}

        {chartType === 'bar' && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
                formatter={(value: number) => [`${value.toFixed(1)}`, 'Score']}
              />
              <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                {barData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}

        {chartType === 'pie' && (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={90}
                paddingAngle={3}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value.toFixed(0)}`}
              >
                {pieData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8 }}
                formatter={(value: number) => [`${value.toFixed(1)}`, 'Score']}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Final Score</span>
          <span className="text-lg font-bold text-primary-600">{candidate.final_score.toFixed(1)}</span>
        </div>
      </div>
    </div>
  )
}

export default memo(ScoreBreakdownChart)
