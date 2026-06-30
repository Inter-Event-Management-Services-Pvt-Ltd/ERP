'use client'

import Link from 'next/link'
import { format } from 'date-fns'
import {
  Users,
  FolderOpen,
  Bell,
  AlertTriangle,
  Archive,
  Activity,
  Calendar,
  FileX,
  ShieldAlert,
} from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { useDirectorOverview } from '@/hooks/use-director'
import { useModuleEnabled } from '@/hooks/use-modules'
import type { DirectorAuditEvent } from '@/types'

function StatRow({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-surface-border last:border-0">
      <span className="text-xs text-text-primary/55 font-sans">{label}</span>
      <span className="text-sm font-mono text-text-primary tabular-nums">{value}</span>
    </div>
  )
}

function SectionCard({
  icon: Icon,
  title,
  href,
  children,
}: {
  icon: React.ElementType
  title: string
  href?: string
  children: React.ReactNode
}) {
  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon size={14} className="text-accent-saffron" aria-hidden="true" />
          <h2 className="text-xs font-mono uppercase tracking-widest text-text-primary/55">{title}</h2>
        </div>
        {href && (
          <Link
            href={href}
            className="text-[10px] font-mono uppercase tracking-wider text-accent-saffron hover:text-accent-saffron/70 transition-colors"
          >
            View all
          </Link>
        )}
      </div>
      {children}
    </div>
  )
}

function CountCard({
  icon: Icon,
  label,
  count,
  href,
  variant = 'normal',
}: {
  icon: React.ElementType
  label: string
  count: number
  href: string
  variant?: 'normal' | 'warning' | 'critical'
}) {
  const valueClass =
    variant === 'critical'
      ? 'text-accent-critical'
      : variant === 'warning'
      ? 'text-accent-warning'
      : 'text-text-primary'

  return (
    <Link
      href={href}
      className="rounded-lg border border-surface-border bg-surface-raised p-4 flex flex-col gap-2 hover:border-accent-saffron/40 transition-colors group"
    >
      <div className="flex items-center gap-2">
        <Icon size={14} className="text-accent-saffron" aria-hidden="true" />
        <span className="text-xs font-mono uppercase tracking-widest text-text-primary/55">{label}</span>
      </div>
      <span className={`text-3xl font-mono tabular-nums font-semibold ${valueClass}`}>{count}</span>
    </Link>
  )
}

function AuditEventRow({ event }: { event: DirectorAuditEvent }) {
  return (
    <tr className="border-b border-surface-border last:border-0">
      <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
        {event.actor ? (
          <>
            <span className="text-xs text-text-primary/40 font-mono mr-2">{event.actor.employee_code}</span>
            <span className="text-xs text-text-primary">{event.actor.full_name}</span>
          </>
        ) : (
          <span className="text-xs text-text-primary/40 font-mono">System</span>
        )}
      </td>
      <td className="px-4 py-3">
        <span className="font-mono text-xs text-accent-saffron/80">{event.action_code}</span>
      </td>
      <td className="px-4 py-3 text-xs text-text-primary/50 font-mono whitespace-nowrap">
        {event.resource_type}
      </td>
      <td className="px-4 py-3 text-xs text-text-primary/40 font-mono whitespace-nowrap">
        {format(new Date(event.created_at), 'dd MMM HH:mm')}
      </td>
    </tr>
  )
}

function formatMinutes(mins: number): string {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export default function DirectorDashboardPage() {
  const { data: overview, isLoading, error, refetch } = useDirectorOverview()
  const attendanceEnabled = useModuleEnabled('attendance')
  const projectsEnabled = useModuleEnabled('projects')
  const archiveEnabled = useModuleEnabled('physical_archive')
  const documentsEnabled = useModuleEnabled('documents')

  return (
    <AppShell>
      <PageHeader
        title="Director Dashboard"
        subtitle={overview ? `Updated ${format(new Date(overview.generated_at), 'HH:mm')}` : 'Overview'}
      />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={10} />}

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

        {!isLoading && !error && overview && (
          <div className="space-y-4">
            {/* Row 1 — Attendance + Projects */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SectionCard
                icon={Users}
                title="Attendance Today"
                href={attendanceEnabled ? '/director/attendance' : undefined}
              >
                {attendanceEnabled ? (
                  <div className="py-2">
                    <StatRow label="Checked in" value={overview.attendance.checked_in_count} />
                    <StatRow label="Checked out" value={overview.attendance.checked_out_count} />
                    <StatRow label="Absent / not checked in" value={overview.attendance.absent_or_not_checked_in_count} />
                  </div>
                ) : (
                  <div className="flex items-center gap-2 py-3">
                    <span className="text-xs font-mono uppercase tracking-wider text-text-primary/30 border border-surface-border rounded px-2 py-0.5">
                      Coming Soon
                    </span>
                    <span className="text-xs font-sans text-text-primary/35">
                      Attendance rollout not yet active
                    </span>
                  </div>
                )}
              </SectionCard>

              <SectionCard icon={FolderOpen} title="Projects" href={projectsEnabled ? '/director/projects' : undefined}>
                {projectsEnabled ? (
                  <>
                    <StatRow label="Active" value={overview.projects.active_count} />
                    <StatRow label="Planning" value={overview.projects.planning_count} />
                    <StatRow label="Completed" value={overview.projects.completed_count} />
                    <StatRow label="Archived" value={overview.projects.archived_count} />
                  </>
                ) : (
                  <div className="flex items-center gap-2 py-3">
                    <span className="text-xs font-mono uppercase tracking-wider text-text-primary/30 border border-surface-border rounded px-2 py-0.5">
                      Coming Soon
                    </span>
                    <span className="text-xs font-sans text-text-primary/35">Not active for this rollout</span>
                  </div>
                )}
              </SectionCard>
            </div>

            {/* Row 2 — Quick counts + Physical archive */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <CountCard
                icon={Bell}
                label="Pending approvals"
                count={overview.pending_approval_count}
                href="/director/approvals"
                variant={overview.pending_approval_count > 0 ? 'warning' : 'normal'}
              />
              <CountCard
                icon={AlertTriangle}
                label="Overdue tasks"
                count={overview.overdue_task_count}
                href="/director/tasks"
                variant={overview.overdue_task_count > 0 ? 'critical' : 'normal'}
              />

              <SectionCard icon={Archive} title="Physical Archive" href={archiveEnabled ? '/director/archive' : undefined}>
                {archiveEnabled ? (
                  <>
                    <StatRow label="Checked out" value={overview.physical_archive.checked_out_count} />
                    <StatRow label="Overdue returns" value={overview.physical_archive.overdue_return_count} />
                    <StatRow label="Verification due" value={overview.physical_archive.verification_due_count} />
                    <StatRow label="Missing" value={overview.physical_archive.missing_count} />
                  </>
                ) : (
                  <div className="flex items-center gap-2 py-3">
                    <span className="text-xs font-mono uppercase tracking-wider text-text-primary/30 border border-surface-border rounded px-2 py-0.5">
                      Coming Soon
                    </span>
                    <span className="text-xs font-sans text-text-primary/35">Not active for this rollout</span>
                  </div>
                )}
              </SectionCard>
            </div>

            {/* Row 3 — Recent audit events */}
            {overview.recent_audit_events.length > 0 && (
              <SectionCard icon={Activity} title="Recent Activity" href="/director/audit">
                <div className="overflow-x-auto -mx-4 -mb-4">
                  <table className="w-full text-sm font-sans">
                    <thead>
                      <tr className="border-b border-surface-border">
                        {['Actor', 'Action', 'Resource', 'Time'].map((h) => (
                          <th
                            key={h}
                            scope="col"
                            className="px-4 py-2 text-left text-xs font-semibold text-text-primary/40 uppercase tracking-wider whitespace-nowrap"
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {overview.recent_audit_events.map((ev) => (
                        <AuditEventRow key={ev.id} event={ev} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </SectionCard>
            )}

            {overview.recent_audit_events.length === 0 && (
              <SectionCard icon={Activity} title="Recent Activity">
                <p className="text-xs text-text-primary/40 py-4 text-center font-sans">No recent audit events.</p>
              </SectionCard>
            )}

            {/* Row 4 — Quick links to extended metrics (hidden when module is disabled) */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Link
                href="/director/upcoming-events"
                className="rounded-lg border border-surface-border bg-surface-raised p-4 flex items-center gap-3 hover:border-accent-saffron/40 transition-colors"
              >
                <Calendar size={14} className="text-accent-saffron flex-none" aria-hidden="true" />
                <div>
                  <p className="text-xs font-mono uppercase tracking-widest text-text-primary/55">Upcoming Events</p>
                  <p className="text-xs text-text-primary/40 mt-0.5">Calendar feed</p>
                </div>
              </Link>
              {documentsEnabled && (
                <Link
                  href="/director/missing-docs"
                  className="rounded-lg border border-surface-border bg-surface-raised p-4 flex items-center gap-3 hover:border-accent-critical/40 transition-colors"
                >
                  <FileX size={14} className="text-accent-critical flex-none" aria-hidden="true" />
                  <div>
                    <p className="text-xs font-mono uppercase tracking-widest text-text-primary/55">Missing Documents</p>
                    <p className="text-xs text-text-primary/40 mt-0.5">Required docs not uploaded</p>
                  </div>
                </Link>
              )}
              {archiveEnabled && (
                <Link
                  href="/director/verification-reminders"
                  className="rounded-lg border border-surface-border bg-surface-raised p-4 flex items-center gap-3 hover:border-accent-warning/40 transition-colors"
                >
                  <ShieldAlert size={14} className="text-accent-warning flex-none" aria-hidden="true" />
                  <div>
                    <p className="text-xs font-mono uppercase tracking-widest text-text-primary/55">Verification Reminders</p>
                    <p className="text-xs text-text-primary/40 mt-0.5">Physical files due for check</p>
                  </div>
                </Link>
              )}
            </div>
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
