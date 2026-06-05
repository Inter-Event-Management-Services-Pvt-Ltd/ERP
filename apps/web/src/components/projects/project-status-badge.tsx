import { Badge } from '@/components/status/badge'
import type { BadgeVariant } from '@/types'

const STATUS_VARIANT: Record<string, BadgeVariant> = {
  PLANNING: 'pending',
  ACTIVE: 'active',
  ON_HOLD: 'warning',
  COMPLETED: 'approved',
  CANCELLED: 'rejected',
  ARCHIVED: 'archived',
}

const PRIORITY_VARIANT: Record<string, BadgeVariant> = {
  LOW: 'info',
  NORMAL: 'info',
  HIGH: 'warning',
  CRITICAL: 'critical',
}

interface ProjectStatusBadgeProps {
  code: string
  name: string
  type?: 'status' | 'priority'
}

export function ProjectStatusBadge({
  code,
  name,
  type = 'status',
}: ProjectStatusBadgeProps) {
  const map = type === 'priority' ? PRIORITY_VARIANT : STATUS_VARIANT
  const variant: BadgeVariant = map[code] ?? 'info'
  return <Badge variant={variant}>{name}</Badge>
}
