import { render, screen } from '@testing-library/react'
import { Badge } from '@/components/status/badge'

test('renders the label text', () => {
  render(<Badge variant="active">ACTIVE</Badge>)
  expect(screen.getByText('ACTIVE')).toBeInTheDocument()
})

test('overdue badge has readable text content — not colour-only', () => {
  render(<Badge variant="overdue">OVERDUE</Badge>)
  expect(screen.getByText('OVERDUE')).toBeInTheDocument()
})
