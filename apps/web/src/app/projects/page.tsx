'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Building2 } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { ProjectStatusBadge } from '@/components/projects/project-status-badge'
import { CreateProjectDialog } from '@/components/projects/create-project-dialog'
import { CreateClientDialog } from '@/components/projects/create-client-dialog'
import { SearchInput } from '@/components/ui/search-input'
import { useProjects } from '@/hooks/use-projects'
import { useProjectTypes, useProjectStatuses, usePriorityLevels } from '@/hooks/use-lookups'
import { useMe } from '@/hooks/use-me'
import { format } from 'date-fns'

export default function ProjectsPage() {
  const router = useRouter()
  const { data: user } = useMe()
  const { data: projects, isLoading, error, refetch } = useProjects()
  const { data: projectTypes = [] } = useProjectTypes()
  const { data: projectStatuses = [] } = useProjectStatuses()
  const { data: priorityLevels = [] } = usePriorityLevels()

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreateProject, setShowCreateProject] = useState(false)
  const [showCreateClient, setShowCreateClient] = useState(false)

  const canManage = (user?.isSuperUser || user?.permissions.includes('project.manage')) ?? false

  const filtered = useMemo(() => {
    if (!projects) return []
    return projects.filter((p) => {
      const matchesSearch =
        !search ||
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.project_code.toLowerCase().includes(search.toLowerCase()) ||
        p.client.display_name.toLowerCase().includes(search.toLowerCase())
      const matchesStatus =
        !statusFilter || p.project_status.code === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [projects, search, statusFilter])

  const uniqueStatuses = useMemo(
    () =>
      Array.from(
        new Map(
          (projects ?? []).map((p) => [p.project_status.code, p.project_status])
        ).values()
      ),
    [projects]
  )

  return (
    <AppShell>
      <PageHeader
        title="Projects"
        subtitle={
          projects
            ? `${projects.length} project${projects.length !== 1 ? 's' : ''}`
            : 'All projects'
        }
        actions={
          canManage ? (
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowCreateClient(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans text-text-primary/60 border border-surface-border rounded-md hover:bg-surface-raised hover:text-text-primary transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron"
              >
                <Building2 size={13} aria-hidden="true" />
                New Client
              </button>
              <button
                type="button"
                onClick={() => setShowCreateProject(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans font-medium bg-accent-saffron text-surface-deep rounded-md hover:bg-accent-warning transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
              >
                <Plus size={13} aria-hidden="true" />
                New Project
              </button>
            </div>
          ) : null
        }
      />

      <ContentArea>
        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-5">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search projects…"
            className="w-64"
          />
          {uniqueStatuses.length > 1 && (
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              aria-label="Filter by status"
              className="rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
            >
              <option value="">All statuses</option>
              {uniqueStatuses.map((s) => (
                <option key={s.code} value={s.code}>
                  {s.name}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Content states */}
        {isLoading && <SkeletonScreen rows={6} />}

        {!isLoading && error && (
          <ErrorState
            message={
              error instanceof Error ? error.message : 'Failed to load projects'
            }
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && filtered.length === 0 && (
          <EmptyState
            heading={search || statusFilter ? 'No matching projects' : 'No projects yet'}
            body={
              search || statusFilter
                ? 'Try adjusting your search or filter.'
                : canManage
                ? 'Create your first project to get started.'
                : 'Projects you have access to will appear here.'
            }
          />
        )}

        {!isLoading && !error && filtered.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Code', 'Project', 'Client', 'Status', 'Priority', 'Event Date'].map(
                    (h) => (
                      <th
                        key={h}
                        scope="col"
                        className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap"
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {filtered.map((p, i) => (
                  <tr
                    key={p.id}
                    onClick={() => router.push(`/projects/${p.id}`)}
                    className={`cursor-pointer transition-colors hover:bg-surface-raised border-b border-surface-border last:border-0 ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">
                      {p.project_code}
                    </td>
                    <td className="px-4 py-3 font-sans text-text-primary max-w-xs">
                      <span className="truncate block">{p.name}</span>
                    </td>
                    <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
                      {p.client.display_name}
                    </td>
                    <td className="px-4 py-3">
                      <ProjectStatusBadge
                        code={p.project_status.code}
                        name={p.project_status.name}
                        type="status"
                      />
                    </td>
                    <td className="px-4 py-3">
                      <ProjectStatusBadge
                        code={p.priority_level.code}
                        name={p.priority_level.name}
                        type="priority"
                      />
                    </td>
                    <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap font-mono text-xs">
                      {p.event_date
                        ? format(new Date(p.event_date), 'dd MMM yyyy')
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ContentArea>

      <CreateProjectDialog
        open={showCreateProject}
        onClose={() => setShowCreateProject(false)}
        onCreated={(id) => router.push(`/projects/${id}`)}
        lookups={{ projectTypes, projectStatuses, priorityLevels }}
      />

      <CreateClientDialog
        open={showCreateClient}
        onClose={() => setShowCreateClient(false)}
      />
    </AppShell>
  )
}
