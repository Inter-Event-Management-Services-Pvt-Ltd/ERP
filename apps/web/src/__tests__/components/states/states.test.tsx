import { render, screen } from '@testing-library/react'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { PermissionDenied } from '@/components/states/permission-denied'
import { OfflineBanner } from '@/components/states/offline-banner'

describe('EmptyState', () => {
  test('renders heading and body', () => {
    render(<EmptyState heading="No projects yet" body="Create one to get started." />)
    expect(screen.getByRole('heading', { name: 'No projects yet' })).toBeInTheDocument()
    expect(screen.getByText('Create one to get started.')).toBeInTheDocument()
  })
})

describe('ErrorState', () => {
  test('renders message and retry button', () => {
    const retry = vi.fn()
    render(<ErrorState message="Failed to load." onRetry={retry} />)
    expect(screen.getByText('Failed to load.')).toBeInTheDocument()
    screen.getByRole('button', { name: /retry/i }).click()
    expect(retry).toHaveBeenCalledOnce()
  })
})

describe('PermissionDenied', () => {
  test('renders generic heading without leaking resource details', () => {
    render(<PermissionDenied />)
    expect(screen.getByRole('heading')).toBeInTheDocument()
    // Must not contain a path or ID
    expect(screen.queryByText(/\/[a-z]/)).toBeNull()
  })
})

describe('OfflineBanner', () => {
  test('renders when visible', () => {
    render(<OfflineBanner visible />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  test('renders nothing when not visible', () => {
    const { container } = render(<OfflineBanner visible={false} />)
    expect(container.firstChild).toBeNull()
  })
})
