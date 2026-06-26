'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { format } from 'date-fns'
import { Plus } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ModuleGuard } from '@/components/states/module-guard'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { ProjectStatusBadge } from '@/components/projects/project-status-badge'
import { CreateTaskDialog } from '@/components/tasks/create-task-dialog'
import { useMe } from '@/hooks/use-me'
import { useTasks } from '@/hooks/use-tasks'
import { useTaskStatuses } from '@/hooks/use-lookups'
import { useProjects } from '@/hooks/use-projects'
import type { BadgeVariant, TaskStatusCode } from '@/types'

const STATUS_VARIANT: Record<TaskStatusCode, BadgeVariant> = {
  TODO: 'pending',
  IN_PROGRESS: 'info',
  BLOCKED: 'warning',
  COMPLETED: 'approved',
  CANCELLED: 'archived',
}

export default function TasksPage() {
  const router = useRouter()
  const { data: user } = useMe()
  const canManage = (user?.isSuperUser || user?.permissions.includes('task.manage')) ?? false

  const { data: taskStatuses = [] } = useTaskStatuses()
  const { data: projects = [] } = useProjects()

  const [statusCode, setStatusCode] = useState('')
  const [projectId, setProjectId] = useState('')
  const [assignedToMe, setAssignedToMe] = useState(true)
  const [showCreate, setShowCreate] = useState(false)

  const { data: tasks, isLoading, error, refetch } = useTasks({
    status_code: statusCode || undefined,
    project_id: projectId || undefined,
    assigned_to_me: assignedToMe || undefined,
  })

  return (
    <AppShell>
      <PageHeader
        title="Tasks"
        subtitle={assignedToMe ? 'My tasks' : 'All accessible tasks'}
        actions={
          canManage ? (
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans font-medium bg-accent-saffron text-surface-deep rounded-md hover:bg-accent-warning transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
            >
              <Plus size={13} aria-hidden="true" />
              New Task
            </button>
          ) : null
        }
      />

      <ContentArea>
        <ModuleGuard code="tasks">
        <div className="flex flex-wrap gap-3 mb-5">
          <label className="flex items-center gap-2 px-3 py-2 text-sm font-sans text-text-primary/60 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={assignedToMe}
              onChange={(e) => setAssignedToMe(e.target.checked)}
              className="h-4 w-4 rounded border-surface-border text-accent-saffron focus:outline-none focus:ring-2 focus:ring-accent-saffron"
            />
            Assigned to me
          </label>

          <select
            value={statusCode}
            onChange={(e) => setStatusCode(e.target.value)}
            aria-label="Filter by status"
            className="rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
          >
            <option value="">All statuses</option>
            {taskStatuses.map((s) => (
              <option key={s.id} value={s.code}>
                {s.name}
              </option>
            ))}
          </select>

          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            aria-label="Filter by project"
            className="rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
          >
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {isLoading && <SkeletonScreen rows={6} />}

        {!isLoading && error && (
          <ErrorState
            message={error instanceof Error ? error.message : 'Failed to load tasks'}
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && (tasks ?? []).length === 0 && (
          <EmptyState heading="No tasks found" body="Tasks you create or are assigned to will appear here." />
        )}

        {!isLoading && !error && (tasks ?? []).length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Title', 'Project', 'Status', 'Priority', 'Due', 'Assignees'].map((h) => (
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
                {(tasks ?? []).map((t, i) => (
                  <tr
                    key={t.id}
                    onClick={() => router.push(`/tasks/${t.id}`)}
                    className={`cursor-pointer transition-colors hover:bg-surface-raised border-b border-surface-border last:border-0 ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 font-sans text-text-primary max-w-xs truncate">{t.title}</td>
                    <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
                      {t.project?.name ?? '—'}
                    </td>
                    <td className="px-4 py-3">
                      {t.task_status ? (
                        <Badge variant={STATUS_VARIANT[t.task_status.code as TaskStatusCode] ?? 'info'}>
                          {t.task_status.name}
                        </Badge>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {t.priority_level ? (
                        <ProjectStatusBadge
                          code={t.priority_level.code}
                          name={t.priority_level.name}
                          type="priority"
                        />
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/70 whitespace-nowrap">
                      {t.due_at ? format(new Date(t.due_at), 'dd MMM yyyy HH:mm') : '—'}
                    </td>
                    <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
                      {t.assignees.length > 0
                        ? t.assignees.map((a) => a.full_name).join(', ')
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        </ModuleGuard>
      </ContentArea>

      <CreateTaskDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </AppShell>
  )
}
