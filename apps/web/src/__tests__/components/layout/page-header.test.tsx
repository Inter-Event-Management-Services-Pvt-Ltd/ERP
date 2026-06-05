import { render, screen } from '@testing-library/react'
import { PageHeader } from '@/components/layout/page-header'

test('renders title in h1', () => {
  render(<PageHeader title="Projects" />)
  expect(screen.getByRole('heading', { level: 1, name: 'Projects' })).toBeInTheDocument()
})

test('renders optional subtitle', () => {
  render(<PageHeader title="Projects" subtitle="All projects" />)
  expect(screen.getByText('All projects')).toBeInTheDocument()
})

test('renders children as action slot', () => {
  render(
    <PageHeader title="Projects">
      <button>New Project</button>
    </PageHeader>
  )
  expect(screen.getByRole('button', { name: 'New Project' })).toBeInTheDocument()
})
