'use client'

import { useMe } from './use-me'
import type { UserRole } from '@/types'

export function canAccess(userRoles: UserRole[], allowedRoles: UserRole[]): boolean {
  if (allowedRoles.length === 0) return true
  return userRoles.some((r) => allowedRoles.includes(r))
}

export function useRole() {
  const { data: user } = useMe()
  const roles = user?.roles ?? []

  return {
    roles,
    isDirector: roles.includes('DIRECTOR'),
    isAdmin: roles.some((r) => ['ADMIN', 'SUPER_ADMIN', 'SUPER_USER'].includes(r)),
    isSuperUser: roles.includes('SUPER_USER'),
    isManager: roles.includes('MANAGER'),
    canAccess: (allowedRoles: UserRole[]) => canAccess(roles, allowedRoles),
  }
}
