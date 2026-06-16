'use client'

import { useRole } from '@/hooks/use-role'
import { useMe } from '@/hooks/use-me'
import { PermissionDenied } from '@/components/states/permission-denied'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

/**
 * Wraps /director/* routes. Allows access when the user holds the DIRECTOR role
 * or is a Super User (me.account.is_super_user). Never exposes the route path or
 * resource details in the denied state.
 */
export function DirectorGuard({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading } = useMe()
  const { isDirector } = useRole()
  const canView = isDirector || (user?.isSuperUser ?? false)

  if (isLoading) return <SkeletonScreen rows={6} />
  if (!canView) return <PermissionDenied />

  return <>{children}</>
}
