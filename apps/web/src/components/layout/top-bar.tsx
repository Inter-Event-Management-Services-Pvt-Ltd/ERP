'use client'

import Link from 'next/link'
import { Bell } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useUnreadCount } from '@/hooks/use-notifications'

interface TopBarProps {
  breadcrumb?: React.ReactNode
  className?: string
}

export function TopBar({ breadcrumb, className }: TopBarProps) {
  const unreadCount = useUnreadCount()

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
          aria-label={
            unreadCount > 0
              ? `Notifications — ${unreadCount} unread`
              : 'Notifications'
          }
          className="relative p-2 rounded-md hover:bg-surface-raised transition-colors text-text-primary/60 hover:text-text-primary"
        >
          <Bell size={17} aria-hidden="true" />
          {unreadCount > 0 && (
            <span
              aria-hidden="true"
              className="absolute top-1 right-1 min-w-[14px] h-[14px] px-[3px] flex items-center justify-center rounded-full bg-accent-madder text-[9px] font-mono font-semibold text-text-primary leading-none"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Link>
      </div>
    </header>
  )
}
