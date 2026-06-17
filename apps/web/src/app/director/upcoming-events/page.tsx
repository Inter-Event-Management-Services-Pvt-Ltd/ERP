'use client'

import { format } from 'date-fns'
import { Calendar } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { useDirectorUpcomingEvents } from '@/hooks/use-director'

export default function DirectorUpcomingEventsPage() {
  const { data: events, isLoading, error, refetch } = useDirectorUpcomingEvents({ limit: 100 })

  return (
    <AppShell>
      <PageHeader title="Upcoming Events" subtitle="Calendar feed — Director view" />
      <ContentArea>
        {isLoading && <SkeletonScreen rows={8} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && events?.length === 0 && (
          <EmptyState icon={Calendar} heading="No upcoming events" body="No calendar events found." />
        )}

        {!isLoading && !error && events && events.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Title', 'Type', 'Starts', 'Ends', 'Project', 'Location'].map((h) => (
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
                {events.map((ev, i) => (
                  <tr
                    key={ev.id}
                    className={`border-b border-surface-border last:border-0 ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 font-medium text-text-primary/85">{ev.title}</td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs text-accent-saffron/80">{ev.event_type}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/60 whitespace-nowrap">
                      {format(new Date(ev.starts_at), 'dd MMM yyyy HH:mm')}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/60 whitespace-nowrap">
                      {ev.ends_at ? format(new Date(ev.ends_at), 'dd MMM HH:mm') : '—'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {ev.project_code ? (
                        <span className="text-xs">
                          <span className="font-mono text-text-primary/40 mr-1">{ev.project_code}</span>
                          <span className="text-text-primary/70">{ev.project_name}</span>
                        </span>
                      ) : (
                        <span className="text-text-primary/30">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-text-primary/60 text-xs">
                      {ev.location ?? '—'}
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
