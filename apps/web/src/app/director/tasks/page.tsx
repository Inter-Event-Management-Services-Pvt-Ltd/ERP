'use client'

import { format } from 'date-fns'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { CheckSquare } from 'lucide-react'
import { useDirectorOverdueTasks } from '@/hooks/use-director'

export default function DirectorTasksPage() {
  const { data: tasks, isLoading, error, refetch } = useDirectorOverdueTasks({ limit: 100 })

  return (
    <AppShell>
      <PageHeader title="Overdue Tasks" subtitle="Across all projects" />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={7} />}

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

        {!isLoading && !error && tasks?.length === 0 && (
          <EmptyState
            icon={CheckSquare}
            heading="No overdue tasks"
            body="All tasks are on schedule."
          />
        )}

        {!isLoading && !error && tasks && tasks.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Task', 'Project', 'Assignees', 'Due at'].map((h) => (
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
                {tasks.map((t, i) => (
                  <tr
                    key={t.id}
                    className={`border-b border-surface-border last:border-0 ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 text-text-primary max-w-[260px] truncate whitespace-nowrap">
                      {t.title}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono text-xs text-text-primary/50 mr-1.5">{t.project_code}</span>
                      <span className="text-text-primary/70">{t.project_name}</span>
                    </td>
                    <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
                      {t.assignees || '—'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Badge variant="overdue">
                        {format(new Date(t.due_at), 'dd MMM yyyy')}
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
