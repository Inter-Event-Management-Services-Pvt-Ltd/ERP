'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { FolderOpen, Building2, CalendarDays, ChevronRight, TrendingUp } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ProjectStatusBadge } from '@/components/projects/project-status-badge'
import { useMe } from '@/hooks/use-me'
import { useProjects } from '@/hooks/use-projects'
import { useClients } from '@/hooks/use-clients'
import { format } from 'date-fns'

function greeting(name: string) {
  const h = new Date().getHours()
  const time = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'
  const first = name.split(' ')[0]
  return `${time}, ${first}`
}

export default function DashboardPage() {
  const { data: user, isLoading: userLoading } = useMe()
  const { data: projects = [], isLoading: projectsLoading } = useProjects()
  const { data: clients = [] } = useClients()

  const stats = useMemo(() => {
    const active = projects.filter((p) => p.project_status.code === 'ACTIVE').length
    const planning = projects.filter((p) => p.project_status.code === 'PLANNING').length
    const upcoming = projects.filter(
      (p) => p.event_date && new Date(p.event_date) >= new Date()
    ).length
    return { total: projects.length, active, planning, upcoming }
  }, [projects])

  const recentProjects = useMemo(
    () =>
      [...projects]
        .filter((p) => !p.deleted_at && !p.archived_at)
        .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
        .slice(0, 5),
    [projects]
  )

  const isLoading = userLoading || projectsLoading

  return (
    <AppShell>
      <PageHeader
        title={user ? greeting(user.fullName) : 'Dashboard'}
        subtitle={user?.designation ?? 'Overview'}
      />

      <ContentArea>
        {isLoading ? (
          <SkeletonScreen rows={6} />
        ) : (
          <div className="space-y-6">
            {/* Stats row */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                label="Total Projects"
                value={stats.total}
                icon={<FolderOpen size={15} className="text-accent-saffron" aria-hidden="true" />}
              />
              <StatCard
                label="Active"
                value={stats.active}
                icon={<TrendingUp size={15} className="text-accent-saffron" aria-hidden="true" />}
                highlight={stats.active > 0}
              />
              <StatCard
                label="Planning"
                value={stats.planning}
                icon={<CalendarDays size={15} className="text-accent-saffron" aria-hidden="true" />}
              />
              <StatCard
                label="Clients"
                value={clients.filter((c) => c.is_active).length}
                icon={<Building2 size={15} className="text-accent-saffron" aria-hidden="true" />}
              />
            </div>

            {/* Recent projects */}
            <section aria-labelledby="recent-heading">
              <div className="flex items-center justify-between mb-3">
                <h2
                  id="recent-heading"
                  className="text-xs font-sans font-semibold text-text-primary/50 uppercase tracking-wider"
                >
                  Recent Projects
                </h2>
                <Link
                  href="/projects"
                  className="text-xs font-sans text-accent-saffron hover:text-accent-warning transition-colors"
                >
                  View all
                </Link>
              </div>

              {recentProjects.length === 0 ? (
                <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-8 text-center">
                  <p className="text-sm text-text-primary/40 font-sans">No projects yet.</p>
                  <Link
                    href="/projects"
                    className="mt-2 inline-block text-xs text-accent-saffron hover:text-accent-warning transition-colors"
                  >
                    Create your first project →
                  </Link>
                </div>
              ) : (
                <div className="rounded-lg border border-surface-border overflow-hidden">
                  {recentProjects.map((p, i) => (
                    <Link
                      key={p.id}
                      href={`/projects/${p.id}`}
                      className={`flex items-center justify-between px-4 py-3 hover:bg-surface-raised transition-colors group ${
                        i !== recentProjects.length - 1 ? 'border-b border-surface-border' : ''
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-0.5">
                          <p className="text-sm font-sans text-text-primary truncate">{p.name}</p>
                        </div>
                        <div className="flex items-center gap-3 flex-wrap">
                          <span className="text-xs font-mono text-text-primary/30">{p.project_code}</span>
                          <span className="text-xs font-sans text-text-primary/40">{p.client.display_name}</span>
                          {p.event_date && (
                            <span className="text-xs font-mono text-text-primary/30">
                              {format(new Date(p.event_date), 'dd MMM yyyy')}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-3 flex-none ml-4">
                        <ProjectStatusBadge
                          code={p.project_status.code}
                          name={p.project_status.name}
                          type="status"
                        />
                        <ChevronRight
                          size={14}
                          className="text-text-primary/20 group-hover:text-text-primary/50 transition-colors"
                          aria-hidden="true"
                        />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </section>

            {/* Quick links */}
            <section aria-labelledby="quick-heading">
              <h2
                id="quick-heading"
                className="text-xs font-sans font-semibold text-text-primary/50 uppercase tracking-wider mb-3"
              >
                Quick Access
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <QuickLink href="/projects" icon={<FolderOpen size={16} aria-hidden="true" />} label="All Projects" sub="Browse and manage projects" />
                <QuickLink href="/archive" icon={<Building2 size={16} aria-hidden="true" />} label="Archive" sub="Physical file tracking" />
              </div>
            </section>
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}

function StatCard({
  label,
  value,
  icon,
  highlight = false,
}: {
  label: string
  value: number
  icon: React.ReactNode
  highlight?: boolean
}) {
  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3 space-y-2">
      <div className="flex items-center gap-1.5">
        {icon}
        <p className="text-xs font-sans text-text-primary/40 uppercase tracking-wider">{label}</p>
      </div>
      <p className={`text-2xl font-mono font-semibold ${highlight ? 'text-accent-saffron' : 'text-text-primary'}`}>
        {value}
      </p>
    </div>
  )
}

function QuickLink({
  href,
  icon,
  label,
  sub,
}: {
  href: string
  icon: React.ReactNode
  label: string
  sub: string
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 rounded-lg border border-surface-border bg-surface-raised px-4 py-3 hover:bg-surface-deep/50 transition-colors group"
    >
      <div className="text-accent-saffron flex-none">{icon}</div>
      <div className="min-w-0">
        <p className="text-sm font-sans font-medium text-text-primary">{label}</p>
        <p className="text-xs font-sans text-text-primary/40">{sub}</p>
      </div>
      <ChevronRight
        size={14}
        className="text-text-primary/20 group-hover:text-text-primary/50 transition-colors ml-auto flex-none"
        aria-hidden="true"
      />
    </Link>
  )
}
