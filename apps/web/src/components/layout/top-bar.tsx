import Link from 'next/link'
import { Bell } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TopBarProps {
  breadcrumb?: React.ReactNode
  className?: string
}

export function TopBar({ breadcrumb, className }: TopBarProps) {
  return (
    <header
      className={cn(
        'flex h-14 flex-none items-center justify-between px-4 bg-surface-deep border-b border-surface-border',
        className
      )}
    >
      <div className="flex items-center gap-3 min-w-0">
        {breadcrumb && (
          <div className="flex items-center gap-1 text-sm text-text-primary/50 min-w-0 truncate">
            {breadcrumb}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1 flex-none">
        <Link
          href="/notifications"
          aria-label="Notifications"
          className="p-2 rounded-md hover:bg-surface-raised transition-colors text-text-primary/60 hover:text-text-primary"
        >
          <Bell size={17} aria-hidden="true" />
        </Link>
      </div>
    </header>
  )
}
