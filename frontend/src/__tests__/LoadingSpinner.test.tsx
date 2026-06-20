import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import LoadingSpinner from '../components/LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders without text', () => {
    const { container } = render(<LoadingSpinner />)
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders with text', () => {
    render(<LoadingSpinner text="Loading..." />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders with different sizes', () => {
    const { rerender, container } = render(<LoadingSpinner size="sm" />)
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()

    rerender(<LoadingSpinner size="lg" text="Big spinner" />)
    expect(screen.getByText('Big spinner')).toBeInTheDocument()
  })
})
