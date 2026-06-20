'use client'

import { useMe } from '@/hooks/use-me'
import { canAccess } from '@/hooks/use-role'
import { PermissionDenied } from '@/components/states/permission-denied'
import type { UserRole } from '@/types'

const ADMIN_ROLES: UserRole[] = ['ADMIN', 'SUPER_ADMIN', 'SUPER_USER']

/**
 * Wraps /admin/* routes. Allows access when the user is a Super User or holds
 * an admin-capable role (ADMIN, SUPER_ADMIN, SUPER_USER). Never exposes the
 * route path or resource details in the denied state.
 *
 * Children mount immediately so their queries fire in parallel with /v1/me.
 */
export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading } = useMe()
  const canView =
    (user?.isSuperUser ?? false) || canAccess(user?.roles ?? [], ADMIN_ROLES)

  if (!isLoading && !canView) return <PermissionDenied />

  return <>{children}</>
}
