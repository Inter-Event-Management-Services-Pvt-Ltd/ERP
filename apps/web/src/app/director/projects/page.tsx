'use client'

import { format } from 'date-fns'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { useDirectorProjects } from '@/hooks/use-director'
import type { BadgeVariant } from '@/types'

const STATUS_VARIANT: Record<string, BadgeVariant> = {
  ACTIVE: 'active',
  PLANNING: 'info',
  COMPLETED: 'approved',
  ARCHIVED: 'archived',
  ON_HOLD: 'pending',
}

const PRIORITY_VARIANT: Record<string, BadgeVariant> = {
  LOW: 'info',
  NORMAL: 'info',
  HIGH: 'warning',
  URGENT: 'critical',
}

export default function DirectorProjectsPage() {
  const { data: projects, isLoading, error, refetch } = useDirectorProjects({ limit: 100 })

  return (
    <AppShell>
      <PageHeader title="Projects" subtitle="All projects" />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={8} />}

        {!isLoading && error && (
          <ErrorState
            message={
              (error as { code?: string }).code === 'PERMISSION_DENIED'
                ? 'Director access required.'
                : (error as Error).message
            }
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && projects?.length === 0 && (
          <EmptyState heading="No projects found" body="Projects will appear here once they are created." />
        )}

        {!isLoading && !error && projects && projects.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Code', 'Name', 'Client', 'Manager', 'Event Date', 'Status', 'Priority'].map((h) => (
                    <th
                      key={h}
                      scope="col"
                      className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {projects.map((p, i) => (
                  <tr
                    key={p.id}
                    className={`border-b border-surface-border last:border-0 ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/60 whitespace-nowrap">
                      {p.project_code}
                    </td>
                    <td className="px-4 py-3 text-text-primary whitespace-nowrap max-w-[220px] truncate">
                      {p.name}
                    </td>
                    <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
                      {p.client_name}
                    </td>
                    <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
                      {p.project_manager_name}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/60 whitespace-nowrap">
                      {format(new Date(p.event_date), 'dd MMM yyyy')}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={STATUS_VARIANT[p.project_status] ?? 'info'}>
                        {p.project_status.replace(/_/g, ' ')}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={PRIORITY_VARIANT[p.priority_level] ?? 'info'}>
                        {p.priority_level}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
