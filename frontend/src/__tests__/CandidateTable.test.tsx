import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import CandidateTable from '../components/CandidateTable'
import { CandidateProvider } from '../context/CandidateContext'
import type { CandidateScore } from '../types'

const mockCandidates: CandidateScore[] = [
  {
    candidate_id: 'CAND_001',
    rank: 1,
    final_score: 92.5,
    skill_score: 95,
    experience_score: 88,
    education_score: 80,
    semantic_score: 90,
    achievement_score: 92,
    strengths: [],
    weaknesses: [],
    explanation: '',
    profile_summary: 'Senior engineer',
    seniority: 'Senior',
    total_experience_years: 7,
  },
  {
    candidate_id: 'CAND_002',
    rank: 2,
    final_score: 85.0,
    skill_score: 82,
    experience_score: 80,
    education_score: 85,
    semantic_score: 88,
    achievement_score: 78,
    strengths: [],
    weaknesses: [],
    explanation: '',
    profile_summary: 'Mid-level developer',
    seniority: 'Mid',
    total_experience_years: 4,
  },
]

function renderWithProvider(ui: React.ReactElement) {
  return render(<CandidateProvider>{ui}</CandidateProvider>)
}

describe('CandidateTable', () => {
  it('renders table with candidates', () => {
    renderWithProvider(
      <CandidateTable candidates={mockCandidates} onSelect={() => {}} />
    )
    expect(screen.getByText('CAND_001')).toBeInTheDocument()
    expect(screen.getByText('CAND_002')).toBeInTheDocument()
  })

  it('renders column headers', () => {
    renderWithProvider(
      <CandidateTable candidates={mockCandidates} onSelect={() => {}} />
    )
    expect(screen.getByText('Rank')).toBeInTheDocument()
    expect(screen.getByText('Final')).toBeInTheDocument()
    expect(screen.getByText('Semantic')).toBeInTheDocument()
    expect(screen.getByText('Skill')).toBeInTheDocument()
  })

  it('renders candidate count', () => {
    renderWithProvider(
      <CandidateTable candidates={mockCandidates} onSelect={() => {}} />
    )
    expect(screen.getByText(/Ranked Candidates \(2\)/)).toBeInTheDocument()
  })

  it('returns null for empty candidates', () => {
    const { container } = renderWithProvider(
      <CandidateTable candidates={[]} onSelect={() => {}} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('calls onSelect when row clicked', () => {
    const onSelect = vi.fn()
    renderWithProvider(
      <CandidateTable candidates={mockCandidates} onSelect={onSelect} />
    )
    screen.getByText('CAND_001').click()
    expect(onSelect).toHaveBeenCalled()
  })
})
