'use client'

import { useQuery } from '@tanstack/react-query'
import { fetchModules } from '@/lib/api'
import type { ModuleCode } from '@/types'

export const MODULES_QUERY_KEY = ['modules'] as const

/** Fetches /v1/modules once per session (unauthenticated). Stale for 5 minutes. */
export function useModules() {
  return useQuery({
    queryKey: MODULES_QUERY_KEY,
    queryFn: fetchModules,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

/**
 * Returns true while loading (fail-open) and true for unknown module codes.
 * Only returns false when the backend explicitly marks a known code as disabled.
 */
export function useModuleEnabled(code: ModuleCode): boolean {
  const { data } = useModules()
  if (!data) return true
  const flag = data.find(f => f.code === code)
  return flag?.enabled ?? true
}
