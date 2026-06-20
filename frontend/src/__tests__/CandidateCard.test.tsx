import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import CandidateCard from '../components/CandidateCard'
import { CandidateProvider } from '../context/CandidateContext'
import type { CandidateScore } from '../types'

const mockCandidate: CandidateScore = {
  candidate_id: 'CAND_001',
  rank: 1,
  final_score: 92.5,
  skill_score: 95,
  experience_score: 88,
  education_score: 80,
  semantic_score: 90,
  achievement_score: 92,
  strengths: ['Strong Python expertise', '5 years experience'],
  weaknesses: ['Limited cloud experience'],
  explanation: 'Top candidate',
  profile_summary: 'Senior backend engineer with Python expertise',
  seniority: 'Senior',
  total_experience_years: 7,
}

function renderWithProvider(ui: React.ReactElement) {
  return render(<CandidateProvider>{ui}</CandidateProvider>)
}

describe('CandidateCard', () => {
  it('renders candidate ID', () => {
    renderWithProvider(
      <CandidateCard candidate={mockCandidate} onViewDetails={() => {}} />
    )
    expect(screen.getByText('CAND_001')).toBeInTheDocument()
  })

  it('renders final score', () => {
    renderWithProvider(
      <CandidateCard candidate={mockCandidate} onViewDetails={() => {}} />
    )
    expect(screen.getByText('92.5')).toBeInTheDocument()
  })

  it('renders seniority badge', () => {
    renderWithProvider(
      <CandidateCard candidate={mockCandidate} onViewDetails={() => {}} />
    )
    expect(screen.getByText('Senior')).toBeInTheDocument()
  })

  it('renders strengths', () => {
    renderWithProvider(
      <CandidateCard candidate={mockCandidate} onViewDetails={() => {}} />
    )
    expect(screen.getByText('Strong Python expertise')).toBeInTheDocument()
  })

  it('renders experience years', () => {
    renderWithProvider(
      <CandidateCard candidate={mockCandidate} onViewDetails={() => {}} />
    )
    expect(screen.getByText('7y exp')).toBeInTheDocument()
  })

  it('calls onViewDetails when View Details clicked', () => {
    const onView = vi.fn()
    renderWithProvider(
      <CandidateCard candidate={mockCandidate} onViewDetails={onView} />
    )
    screen.getByText('View Details').click()
    expect(onView).toHaveBeenCalledWith(mockCandidate)
  })
})
