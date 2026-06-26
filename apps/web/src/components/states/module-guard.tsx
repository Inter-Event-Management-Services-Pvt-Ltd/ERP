'use client'

import type { ReactNode } from 'react'
import type { ModuleCode } from '@/types'
import { useModuleEnabled } from '@/hooks/use-modules'
import { ModuleDisabledState } from './module-disabled-state'

interface ModuleGuardProps {
  code: ModuleCode
  children: ReactNode
}

/** Renders children when the module is enabled; shows ModuleDisabledState otherwise. */
export function ModuleGuard({ code, children }: ModuleGuardProps) {
  const enabled = useModuleEnabled(code)
  if (!enabled) return <ModuleDisabledState />
  return <>{children}</>
}
