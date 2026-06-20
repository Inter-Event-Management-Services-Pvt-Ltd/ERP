'use client'

import Link from 'next/link'
import {
  Users,
  ShieldCheck,
  FolderOpen,
  Archive,
  Building2,
  Layers,
  ScrollText,
} from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { useMe } from '@/hooks/use-me'

interface AdminSection {
  label: string
  description: string
  href: string
  icon: React.ElementType
  requireManage?: string
}

const ADMIN_SECTIONS: AdminSection[] = [
  {
    label: 'Employees',
    description: 'Manage employee records, statuses, and role assignments.',
    href: '/admin/employees',
    icon: Users,
    requireManage: 'employee.manage',
  },
  {
    label: 'Policies',
    description: 'Create and update ABAC policies controlling resource access.',
    href: '/admin/policies',
    icon: ShieldCheck,
    requireManage: 'policy.manage',
  },
  {
    label: 'Folder Templates',
    description: 'Define reusable folder structures applied to new projects.',
    href: '/admin/folder-templates',
    icon: FolderOpen,
  },
  {
    label: 'Archive Locations',
    description: 'Edit archive room names and physical storage locations.',
    href: '/admin/archive-locations',
    icon: Archive,
  },
  {
    label: 'Departments',
    description: 'View department list used for employee assignments.',
    href: '/admin/departments',
    icon: Building2,
  },
  {
    label: 'Roles',
    description: 'View all system roles and their defined permissions.',
    href: '/admin/roles',
    icon: Layers,
  },
  {
    label: 'Audit Log',
    description: 'Browse and filter the full system audit event trail.',
    href: '/admin/audit',
    icon: ScrollText,
  },
]

export default function AdminPage() {
  const { data: user } = useMe()
  const isSuperUser = user?.isSuperUser ?? false
  const permissions = user?.permissions ?? []

  return (
    <AppShell>
      <PageHeader
        title="Admin"
        subtitle="System administration and configuration"
      />
      <ContentArea>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {ADMIN_SECTIONS.map((section) => {
            const canManage =
              isSuperUser ||
              !section.requireManage ||
              permissions.includes(section.requireManage)

            return (
              <Link
                key={section.href}
                href={section.href}
                className="group flex flex-col gap-3 p-5 rounded-xl border border-surface-border bg-surface-raised hover:border-accent-saffron/40 hover:bg-surface-raised/80 transition-colors"
                aria-label={section.label}
              >
                <div className="flex items-center gap-3">
                  <div className="flex-none w-9 h-9 rounded-lg bg-surface-deep flex items-center justify-center text-text-primary/40 group-hover:text-accent-saffron transition-colors">
                    <section.icon size={18} aria-hidden="true" />
                  </div>
                  <div className="flex flex-col gap-0.5 min-w-0">
                    <span className="text-sm font-medium text-text-primary/85 group-hover:text-text-primary transition-colors">
                      {section.label}
                    </span>
                    {!canManage && (
                      <span className="text-[10px] font-mono text-text-primary/30 uppercase tracking-wide">
                        Read only
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-xs text-text-primary/45 leading-relaxed">
                  {section.description}
                </p>
              </Link>
            )
          })}
        </div>
      </ContentArea>
    </AppShell>
  )
}
