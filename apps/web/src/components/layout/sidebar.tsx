'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  FolderOpen,
  Archive,
  Clock,
  CheckSquare,
  CalendarDays,
  Bell,
  ShieldCheck,
  BarChart3,
  LogOut,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useMe } from '@/hooks/use-me'
import { canAccess } from '@/hooks/use-role'
import { createClient } from '@/lib/supabase/client'
import { ConfirmDialog } from '@/components/status/confirm-dialog'
import type { UserRole } from '@/types'

interface NavItem {
  label: string
  href: string
  icon: React.ElementType
  allowedRoles?: UserRole[]
}

const NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: 'Workspace',
    items: [
      { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { label: 'Projects', href: '/projects', icon: FolderOpen },
      { label: 'Archive', href: '/archive', icon: Archive },
    ],
  },
  {
    label: 'People',
    items: [
      { label: 'Attendance', href: '/attendance', icon: Clock },
      { label: 'Tasks', href: '/tasks', icon: CheckSquare },
      { label: 'Calendar', href: '/calendar', icon: CalendarDays },
    ],
  },
  {
    label: 'Approvals',
    items: [{ label: 'Approvals', href: '/approvals', icon: Bell }],
  },
  {
    label: 'Admin',
    items: [
      {
        label: 'Admin',
        href: '/admin',
        icon: ShieldCheck,
        allowedRoles: ['ADMIN', 'SUPER_ADMIN', 'SUPER_USER'],
      },
    ],
  },
  {
    label: 'Director',
    items: [
      {
        label: 'Director',
        href: '/director',
        icon: BarChart3,
        allowedRoles: ['DIRECTOR'],
      },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { data: user } = useMe()
  const roles = user?.roles ?? []
  const [confirmSignOut, setConfirmSignOut] = useState(false)

  const isSuperUser = user?.isSuperUser ?? false

  const isActive = (href: string) =>
    href === '/dashboard' ? pathname === href : pathname.startsWith(href)

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    window.location.href = '/login'
  }

  return (
    <nav
      aria-label="Main navigation"
      className={cn(
        'group/sidebar flex flex-col h-full bg-surface-deep border-r border-surface-border flex-none',
        'w-11 hover:w-[200px] transition-[width] duration-180 ease-out overflow-hidden'
      )}
    >
      {/* Logo — "i" collapsed, "IEMS" expanded */}
      <div className="flex h-14 flex-none items-center px-3 border-b border-surface-border overflow-hidden">
        <span className="font-mono text-accent-saffron font-semibold tracking-widest whitespace-nowrap select-none">
          <span className="group-hover/sidebar:hidden text-sm">i</span>
          <span className="hidden group-hover/sidebar:inline text-sm">IEMS</span>
        </span>
      </div>

      {/* Nav groups */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden py-2 space-y-0.5">
        {NAV_GROUPS.map((group) => {
          const visible = group.items.filter(
            (item) =>
              !item.allowedRoles || isSuperUser || canAccess(roles, item.allowedRoles)
          )
          if (visible.length === 0) return null

          return (
            <div key={group.label}>
              {visible.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-label={item.label}
                  className={cn(
                    'flex items-center gap-3 mx-1 px-2 py-2.5 rounded-md transition-colors duration-100 whitespace-nowrap overflow-hidden',
                    isActive(item.href)
                      ? 'bg-accent-madder text-text-primary'
                      : 'text-text-primary/55 hover:bg-surface-raised hover:text-text-primary'
                  )}
                >
                  <item.icon size={18} aria-hidden="true" className="flex-none" />
                  <span className="text-sm font-sans opacity-0 group-hover/sidebar:opacity-100 transition-opacity duration-180">
                    {item.label}
                  </span>
                </Link>
              ))}
            </div>
          )
        })}
      </div>

      {/* Footer — always rendered so sign-out is reachable even if GET /v1/me fails.
          px-1 outer + px-1 inner = 8px each side, leaving 28px at w-11 for the 28px avatar/icon. */}
      <div className="flex-none border-t border-surface-border py-2 px-1 space-y-0.5">
        {user && (
          <div className="flex items-center gap-3 px-1 py-1.5 rounded-md overflow-hidden">
            <div className="w-7 h-7 rounded-full bg-accent-madder flex-none flex items-center justify-center text-xs font-mono text-text-primary uppercase">
              {user.fullName.charAt(0)}
            </div>
            <div className="opacity-0 group-hover/sidebar:opacity-100 transition-opacity duration-180 min-w-0">
              <p className="text-xs text-text-primary truncate leading-tight">{user.fullName}</p>
              <p className="text-[10px] text-text-primary/40 font-mono truncate">{user.employeeCode}</p>
            </div>
          </div>
        )}
        <button
          onClick={() => setConfirmSignOut(true)}
          aria-label="Sign out"
          className="flex items-center gap-3 w-full px-1 py-2 rounded-md overflow-hidden text-text-primary/40 hover:text-text-primary/70 hover:bg-surface-raised transition-colors"
        >
          <LogOut size={16} aria-hidden="true" className="flex-none" />
          <span className="text-xs font-sans opacity-0 group-hover/sidebar:opacity-100 transition-opacity duration-180">
            Sign out
          </span>
        </button>
      </div>

      <ConfirmDialog
        open={confirmSignOut}
        title="Sign out?"
        description="You'll be returned to the login screen."
        confirmLabel="Sign out"
        onConfirm={handleSignOut}
        onCancel={() => setConfirmSignOut(false)}
      />
    </nav>
  )
}
