'use client'

import { use } from 'react'
import Link from 'next/link'
import { FolderOpen, Calendar, MapPin, Building2, ChevronRight } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { ProjectStatusBadge } from '@/components/projects/project-status-badge'
import { ProjectMembersPanel } from '@/components/projects/project-members-panel'
import { useProject, useProjectMembers } from '@/hooks/use-projects'
import { useMe } from '@/hooks/use-me'
import { format } from 'date-fns'

interface Props {
  params: Promise<{ id: string }>
}

export default function ProjectDetailPage({ params }: Props) {
  const { id } = use(params)
  const { data: user } = useMe()
  const { data: project, isLoading, error, refetch } = useProject(id)
  const { data: members = [] } = useProjectMembers(id)

  const canManage = (user?.isSuperUser || user?.permissions.includes('project.manage')) ?? false

  return (
    <AppShell>
      {isLoading && (
        <>
          <PageHeader title="Loading…" />
          <ContentArea>
            <SkeletonScreen rows={8} />
          </ContentArea>
        </>
      )}

      {!isLoading && error && (
        <>
          <PageHeader title="Project" />
          <ContentArea>
            <ErrorState
              message={error instanceof Error ? error.message : 'Failed to load project'}
              onRetry={() => refetch()}
            />
          </ContentArea>
        </>
      )}

      {!isLoading && project && (
        <>
          <PageHeader
            title={project.name}
            subtitle={
              <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-text-primary/40 font-sans">
                <Link href="/projects" className="hover:text-text-primary/70 transition-colors">
                  Projects
                </Link>
                <ChevronRight size={12} aria-hidden="true" />
                <span className="text-text-primary/60">{project.name}</span>
              </nav>
            }
          />

          <ContentArea>
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <InfoCard
                  icon={<Building2 size={14} className="text-accent-saffron" aria-hidden="true" />}
                  label="Client"
                  value={project.client.display_name}
                  sub={project.client.client_code}
                />
                <InfoCard
                  icon={<Calendar size={14} className="text-accent-saffron" aria-hidden="true" />}
                  label="Event Date"
                  value={
                    project.event_date
                      ? format(new Date(project.event_date), 'dd MMMM yyyy')
                      : '—'
                  }
                />
                <InfoCard
                  icon={<MapPin size={14} className="text-accent-saffron" aria-hidden="true" />}
                  label="Venue"
                  value={project.venue}
                />
                <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3 space-y-2">
                  <p className="text-xs text-text-primary/40 font-sans uppercase tracking-wider">
                    Status &amp; Priority
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <ProjectStatusBadge
                      code={project.project_status.code}
                      name={project.project_status.name}
                      type="status"
                    />
                    <ProjectStatusBadge
                      code={project.priority_level.code}
                      name={project.priority_level.name}
                      type="priority"
                    />
                  </div>
                </div>
              </div>

              {project.description && (
                <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3">
                  <p className="text-xs text-text-primary/40 font-sans uppercase tracking-wider mb-2">
                    Description
                  </p>
                  <p className="text-sm font-sans text-text-primary/80 leading-relaxed">
                    {project.description}
                  </p>
                </div>
              )}

              <Link
                href={`/projects/${id}/documents`}
                className="flex items-center justify-between rounded-lg border border-surface-border bg-surface-raised px-4 py-3 hover:bg-surface-deep/50 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <FolderOpen size={16} className="text-accent-saffron" aria-hidden="true" />
                  <div>
                    <p className="text-sm font-sans font-medium text-text-primary">
                      Documents &amp; Folders
                    </p>
                    <p className="text-xs text-text-primary/40 font-sans">
                      Browse the project folder tree
                    </p>
                  </div>
                </div>
                <ChevronRight
                  size={14}
                  className="text-text-primary/30 group-hover:text-text-primary/60 transition-colors"
                  aria-hidden="true"
                />
              </Link>

              <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-4">
                <ProjectMembersPanel
                  projectId={id}
                  members={members}
                  canManage={canManage}
                />
              </div>

              <dl className="flex flex-wrap gap-x-6 gap-y-1 text-xs font-mono text-text-primary/30">
                <div className="flex gap-1">
                  <dt>Code:</dt>
                  <dd>{project.project_code}</dd>
                </div>
                <div className="flex gap-1">
                  <dt>Type:</dt>
                  <dd>{project.project_type.name}</dd>
                </div>
                <div className="flex gap-1">
                  <dt>Created:</dt>
                  <dd>{format(new Date(project.created_at), 'dd MMM yyyy')}</dd>
                </div>
              </dl>
            </div>
          </ContentArea>
        </>
      )}
    </AppShell>
  )
}

function InfoCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode
  label: string
  value: string
  sub?: string
}) {
  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3 space-y-1">
      <div className="flex items-center gap-1.5">
        {icon}
        <p className="text-xs text-text-primary/40 font-sans uppercase tracking-wider">
          {label}
        </p>
      </div>
      <p className="text-sm font-sans text-text-primary font-medium leading-snug">{value}</p>
      {sub && <p className="text-xs font-mono text-text-primary/30">{sub}</p>}
    </div>
  )
}
