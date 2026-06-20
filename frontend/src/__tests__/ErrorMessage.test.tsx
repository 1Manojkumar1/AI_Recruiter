import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ErrorMessage from '../components/ErrorMessage'

describe('ErrorMessage', () => {
  it('renders error message', () => {
    render(<ErrorMessage message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders error title', () => {
    render(<ErrorMessage message="Test error" />)
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('renders dismiss button when onDismiss provided', () => {
    const onDismiss = () => {}
    render(<ErrorMessage message="Test" onDismiss={onDismiss} />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('does not render dismiss button without onDismiss', () => {
    render(<ErrorMessage message="Test" />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
