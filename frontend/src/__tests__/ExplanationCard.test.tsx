import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ExplanationCard from '../components/ExplanationCard'
import type { ExplanationResponse } from '../types'

const mockExplanation: ExplanationResponse = {
  candidate_id: 'CAND_001',
  strengths: ['Strong Python skills', 'Great experience'],
  weaknesses: ['Limited cloud exposure'],
  summary: 'This candidate is a strong fit for the role.',
  recommendation: 'Recommend for interview',
  scores: { skill: 95, experience: 88 },
}

describe('ExplanationCard', () => {
  it('renders strengths', () => {
    render(<ExplanationCard explanation={mockExplanation} />)
    expect(screen.getByText('Strong Python skills')).toBeInTheDocument()
    expect(screen.getByText('Great experience')).toBeInTheDocument()
  })

  it('renders weaknesses', () => {
    render(<ExplanationCard explanation={mockExplanation} />)
    expect(screen.getByText('Limited cloud exposure')).toBeInTheDocument()
  })

  it('renders summary', () => {
    render(<ExplanationCard explanation={mockExplanation} />)
    expect(screen.getByText('This candidate is a strong fit for the role.')).toBeInTheDocument()
  })

  it('renders recommendation', () => {
    render(<ExplanationCard explanation={mockExplanation} />)
    expect(screen.getByText('Recommend for interview')).toBeInTheDocument()
  })

  it('renders rank when provided', () => {
    render(<ExplanationCard explanation={mockExplanation} rank={1} />)
    expect(screen.getByText(/Why ranked #1/)).toBeInTheDocument()
  })

  it('renders candidate name when provided', () => {
    render(<ExplanationCard explanation={mockExplanation} candidateName="John Doe" />)
    expect(screen.getByText('John Doe')).toBeInTheDocument()
  })
})
