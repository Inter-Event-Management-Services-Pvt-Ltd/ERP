'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchMe, fetchPermissions } from '@/lib/api'
import type { AuthUser } from '@/types'

export const ME_QUERY_KEY = ['me'] as const

/** Primary auth context — role and permissions come from the backend only. */
export function useMe() {
  return useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: async (): Promise<AuthUser> => {
      const me = await fetchMe()
      return {
        supabaseId: me.auth_user_id,
        employeeId: me.employee.id,
        employeeCode: me.employee.employee_code,
        fullName: me.employee.full_name,
        email: me.employee.official_email,
        designation: me.employee.designation,
        roles: me.roles,
        permissions: me.permissions,
        isActive: me.account.is_active,
        isSuperUser: me.account.is_super_user,
      }
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export const PERMISSIONS_QUERY_KEY = ['me', 'permissions'] as const

export function usePermissions() {
  return useQuery({
    queryKey: PERMISSIONS_QUERY_KEY,
    queryFn: fetchPermissions,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}
