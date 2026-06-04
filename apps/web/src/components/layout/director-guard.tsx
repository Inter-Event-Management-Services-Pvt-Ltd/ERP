'use client'

import { useRole } from '@/hooks/use-role'
import { useMe } from '@/hooks/use-me'
import { PermissionDenied } from '@/components/states/permission-denied'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

/**
 * Wraps /director/* routes. Shows PermissionDenied if the user's roles from
 * GET /v1/me do not include DIRECTOR. Never exposes the route path or resource
 * details in the denied state.
 */
export function DirectorGuard({ children }: { children: React.ReactNode }) {
  const { isLoading } = useMe()
  const { isDirector } = useRole()

  if (isLoading) return <SkeletonScreen rows={6} />
  if (!isDirector) return <PermissionDenied />

  return <>{children}</>
}
