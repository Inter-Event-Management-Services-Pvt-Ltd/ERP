'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { FolderOpen, Calendar, MapPin, Building2, ChevronRight, Archive, ArchiveRestore, Loader2, Boxes } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { ConfirmDialog } from '@/components/status/confirm-dialog'
import { ProjectStatusBadge } from '@/components/projects/project-status-badge'
import { ProjectMembersPanel } from '@/components/projects/project-members-panel'
import { ArchivePhysicalFileDialog } from '@/components/projects/archive-physical-file-dialog'
import { PhysicalArchivePanel } from '@/components/projects/physical-archive-panel'
import { useProject, useProjectMembers, useUpdateProject } from '@/hooks/use-projects'
import { useProjectStatuses } from '@/hooks/use-lookups'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import { format } from 'date-fns'

interface Props {
  params: Promise<{ id: string }>
}

export default function ProjectDetailPage({ params }: Props) {
  const { id } = use(params)
  const router = useRouter()
  const { data: user } = useMe()
  const { data: project, isLoading, error, refetch } = useProject(id)
  const { data: members = [] } = useProjectMembers(id)
  const { data: projectStatuses = [] } = useProjectStatuses()
  const { mutate: updateProject, isPending: updating } = useUpdateProject(id)

  const [statusError, setStatusError] = useState<string | null>(null)
  const [archiveError, setArchiveError] = useState<string | null>(null)
  const [showArchiveConfirm, setShowArchiveConfirm] = useState(false)
  const [showArchivePhysicalFile, setShowArchivePhysicalFile] = useState(false)

  const canManage = (user?.isSuperUser || user?.permissions.includes('project.manage')) ?? false
  const canArchivePhysicalFile =
    canManage && ((user?.isSuperUser || user?.permissions.includes('archive.manage')) ?? false)
  const isArchived = Boolean(project?.archived_at)

  function handleStatusChange(statusId: string) {
    if (!statusId || statusId === project?.project_status_id) return
    setStatusError(null)
    updateProject(
      { project_status_id: statusId },
      { onError: (err) => setStatusError(apiErrorMessage(err)) }
    )
  }

  function handleArchive() {
    setArchiveError(null)
    updateProject(
      { archived_at: new Date().toISOString() },
      {
        onSuccess: () => setShowArchiveConfirm(false),
        onError: (err) => setArchiveError(apiErrorMessage(err)),
      }
    )
  }

  function handleUnarchive() {
    setArchiveError(null)
    updateProject(
      { archived_at: null },
      { onError: (err) => setArchiveError(apiErrorMessage(err)) }
    )
  }

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
            actions={
              canManage ? (
                isArchived ? (
                  <button
                    type="button"
                    onClick={handleUnarchive}
                    disabled={updating}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans font-medium text-text-primary/70 border border-surface-border rounded-md hover:bg-surface-raised hover:text-text-primary disabled:opacity-40 transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron"
                  >
                    {updating ? (
                      <Loader2 size={13} className="animate-spin" aria-hidden="true" />
                    ) : (
                      <ArchiveRestore size={13} aria-hidden="true" />
                    )}
                    Unarchive
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setShowArchiveConfirm(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans font-medium text-text-primary/70 border border-surface-border rounded-md hover:bg-surface-raised hover:text-text-primary transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron"
                  >
                    <Archive size={13} aria-hidden="true" />
                    Archive
                  </button>
                )
              ) : null
            }
          />

          <ContentArea>
            <div className="space-y-6">
              {isArchived && (
                <div className="rounded-lg border border-text-primary/15 bg-surface-raised px-4 py-3 flex items-center gap-2.5">
                  <Archive size={14} className="text-text-primary/40" aria-hidden="true" />
                  <p className="text-sm font-sans text-text-primary/60">
                    This project is archived
                    {project.archived_at && (
                      <> since {format(new Date(project.archived_at), 'dd MMM yyyy')}</>
                    )}
                    .
                  </p>
                </div>
              )}

              {archiveError && (
                <p role="alert" className="text-xs font-sans text-accent-critical">{archiveError}</p>
              )}

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
                  <div className="flex flex-wrap items-center gap-2">
                    {canManage ? (
                      <select
                        aria-label="Project status"
                        value={project.project_status_id}
                        onChange={(e) => handleStatusChange(e.target.value)}
                        disabled={updating}
                        className="rounded-md border border-surface-border bg-surface-base px-2.5 py-1 text-xs font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron disabled:opacity-40"
                      >
                        {projectStatuses.map((s) => (
                          <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                      </select>
                    ) : (
                      <ProjectStatusBadge
                        code={project.project_status.code}
                        name={project.project_status.name}
                        type="status"
                      />
                    )}
                    <ProjectStatusBadge
                      code={project.priority_level.code}
                      name={project.priority_level.name}
                      type="priority"
                    />
                  </div>
                  {statusError && (
                    <p role="alert" className="text-xs font-sans text-accent-critical">{statusError}</p>
                  )}
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

              {canArchivePhysicalFile && (
                <button
                  type="button"
                  onClick={() => setShowArchivePhysicalFile(true)}
                  className="flex w-full items-center justify-between rounded-lg border border-surface-border bg-surface-raised px-4 py-3 hover:bg-surface-deep/50 transition-colors group text-left focus-visible:ring-2 focus-visible:ring-accent-saffron"
                >
                  <div className="flex items-center gap-3">
                    <Boxes size={16} className="text-accent-saffron" aria-hidden="true" />
                    <div>
                      <p className="text-sm font-sans font-medium text-text-primary">
                        Archive Physical File
                      </p>
                      <p className="text-xs text-text-primary/40 font-sans">
                        Register a hard-copy file into the physical archive
                      </p>
                    </div>
                  </div>
                  <ChevronRight
                    size={14}
                    className="text-text-primary/30 group-hover:text-text-primary/60 transition-colors"
                    aria-hidden="true"
                  />
                </button>
              )}

              <PhysicalArchivePanel projectId={id} />

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

          <ConfirmDialog
            open={showArchiveConfirm}
            title="Archive this project?"
            description="The project will be marked as archived. You can unarchive it again at any time from this page."
            confirmLabel={updating ? 'Archiving…' : 'Archive'}
            onConfirm={handleArchive}
            onCancel={() => setShowArchiveConfirm(false)}
          />

          <ArchivePhysicalFileDialog
            open={showArchivePhysicalFile}
            projectId={id}
            onClose={() => setShowArchivePhysicalFile(false)}
            onCreated={(file) => router.push(`/archive/files/${file.id}`)}
          />
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
