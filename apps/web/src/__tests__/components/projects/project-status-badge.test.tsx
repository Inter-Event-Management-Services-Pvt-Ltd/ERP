import { render, screen } from '@testing-library/react'
import { ProjectStatusBadge } from '@/components/projects/project-status-badge'

test('renders planning status', () => {
  render(<ProjectStatusBadge code="PLANNING" name="Planning" type="status" />)
  expect(screen.getByText('Planning')).toBeInTheDocument()
})

test('renders active status', () => {
  render(<ProjectStatusBadge code="ACTIVE" name="Active" type="status" />)
  expect(screen.getByText('Active')).toBeInTheDocument()
})

test('renders priority badge', () => {
  render(<ProjectStatusBadge code="HIGH" name="High" type="priority" />)
  expect(screen.getByText('High')).toBeInTheDocument()
})

test('renders unknown code without throwing', () => {
  render(<ProjectStatusBadge code="UNKNOWN" name="Unknown" type="status" />)
  expect(screen.getByText('Unknown')).toBeInTheDocument()
})
