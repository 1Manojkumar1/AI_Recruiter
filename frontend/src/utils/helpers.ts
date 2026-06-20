/**
 * Utility helper functions for the frontend.
 */

export function getScoreColor(score: number): string {
  if (score >= 90) return 'text-emerald-600'
  if (score >= 80) return 'text-blue-600'
  if (score >= 70) return 'text-amber-600'
  return 'text-gray-500'
}

export function getScoreBgColor(score: number): string {
  if (score >= 90) return 'bg-emerald-50 border-emerald-200'
  if (score >= 80) return 'bg-blue-50 border-blue-200'
  if (score >= 70) return 'bg-amber-50 border-amber-200'
  return 'bg-gray-50 border-gray-200'
}

export function getScoreLabel(score: number): string {
  if (score >= 90) return 'Excellent'
  if (score >= 80) return 'Strong'
  if (score >= 70) return 'Good'
  return 'Average'
}

export function getScoreBadgeColor(score: number): string {
  if (score >= 90) return 'bg-emerald-100 text-emerald-800'
  if (score >= 80) return 'bg-blue-100 text-blue-800'
  if (score >= 70) return 'bg-amber-100 text-amber-800'
  return 'bg-gray-100 text-gray-800'
}

export function formatScore(score: number): string {
  return score.toFixed(1)
}

export function formatTime(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trim() + '...'
}

export function getSeniorityColor(seniority: string): string {
  const level = seniority.toLowerCase()
  if (level === 'executive' || level === 'c-level') return 'bg-purple-100 text-purple-800'
  if (level === 'senior') return 'bg-blue-100 text-blue-800'
  if (level === 'mid') return 'bg-green-100 text-green-800'
  if (level === 'junior') return 'bg-orange-100 text-orange-800'
  return 'bg-gray-100 text-gray-800'
}
