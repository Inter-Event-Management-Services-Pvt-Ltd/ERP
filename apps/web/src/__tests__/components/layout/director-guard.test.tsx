import { vi, describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DirectorGuard } from '@/components/layout/director-guard'

vi.mock('@/hooks/use-me', () => ({
  useMe: vi.fn(),
}))

import { useMe } from '@/hooks/use-me'
const mockUseMe = vi.mocked(useMe)

describe('DirectorGuard', () => {
  it('renders children immediately while /v1/me is loading', () => {
    mockUseMe.mockReturnValue({ data: undefined, isLoading: true } as unknown as ReturnType<typeof useMe>)
    render(<DirectorGuard><span>child content</span></DirectorGuard>)
    expect(screen.getByText('child content')).toBeInTheDocument()
  })

  it('renders children for a user with the DIRECTOR role', () => {
    mockUseMe.mockReturnValue({
      data: { roles: ['DIRECTOR'], isSuperUser: false },
      isLoading: false,
    } as unknown as ReturnType<typeof useMe>)
    render(<DirectorGuard><span>director content</span></DirectorGuard>)
    expect(screen.getByText('director content')).toBeInTheDocument()
  })

  it('renders children for a Super User regardless of role', () => {
    mockUseMe.mockReturnValue({
      data: { roles: [], isSuperUser: true },
      isLoading: false,
    } as unknown as ReturnType<typeof useMe>)
    render(<DirectorGuard><span>super content</span></DirectorGuard>)
    expect(screen.getByText('super content')).toBeInTheDocument()
  })

  it('renders PermissionDenied and hides children for a non-director employee', () => {
    mockUseMe.mockReturnValue({
      data: { roles: ['EMPLOYEE'], isSuperUser: false },
      isLoading: false,
    } as unknown as ReturnType<typeof useMe>)
    render(<DirectorGuard><span>hidden content</span></DirectorGuard>)
    expect(screen.queryByText('hidden content')).not.toBeInTheDocument()
    expect(screen.getByText('Access restricted')).toBeInTheDocument()
  })

  it('does not expose the route path or resource name in the denied state', () => {
    mockUseMe.mockReturnValue({
      data: { roles: [], isSuperUser: false },
      isLoading: false,
    } as unknown as ReturnType<typeof useMe>)
    render(<DirectorGuard><span>secret</span></DirectorGuard>)
    expect(screen.queryByText('secret')).not.toBeInTheDocument()
    expect(screen.queryByText(/\/director/)).not.toBeInTheDocument()
  })
})
