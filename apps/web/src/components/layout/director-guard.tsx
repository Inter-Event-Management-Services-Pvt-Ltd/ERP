'use client'

import { useMe } from '@/hooks/use-me'
import { PermissionDenied } from '@/components/states/permission-denied'

/**
 * Wraps /director/* routes. Allows access when the user holds the DIRECTOR role
 * or is a Super User (me.account.is_super_user). Never exposes the route path or
 * resource details in the denied state.
 *
 * Children mount immediately so their queries fire in parallel with /v1/me rather
 * than waiting for the guard to resolve first.
 */
export function DirectorGuard({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading } = useMe()
  const canView = (user?.roles?.includes('DIRECTOR') ?? false) || (user?.isSuperUser ?? false)

  if (!isLoading && !canView) return <PermissionDenied />

  return <>{children}</>
}
