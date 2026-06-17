'use client'

import { format, isPast } from 'date-fns'
import { ShieldAlert } from 'lucide-react'
import Link from 'next/link'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { useDirectorVerificationReminders } from '@/hooks/use-director'

export default function DirectorVerificationRemindersPage() {
  const { data: items, isLoading, error, refetch } = useDirectorVerificationReminders({ limit: 100 })

  return (
    <AppShell>
      <PageHeader
        title="Verification Reminders"
        subtitle="Physical files with due or overdue verification"
      />
      <ContentArea>
        {isLoading && <SkeletonScreen rows={8} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && items?.length === 0 && (
          <EmptyState
            icon={ShieldAlert}
            heading="No verification reminders"
            body="No physical files have upcoming or overdue verification."
          />
        )}

        {!isLoading && !error && items && items.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['File', 'Project', 'Location', 'Last Verified', 'Next Due'].map((h) => (
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
                {items.map((item, i) => {
                  const overdue = isPast(new Date(item.next_verification_at))
                  return (
                    <tr
                      key={item.id}
                      className={`border-b border-surface-border last:border-0 ${
                        i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                      }`}
                    >
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Link
                          href={`/archive/files/${item.id}`}
                          className="font-mono text-xs text-accent-saffron/80 hover:text-accent-saffron transition-colors"
                        >
                          {item.physical_file_code}
                        </Link>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="font-mono text-xs text-text-primary/40 mr-1">{item.project_code}</span>
                        <span className="text-text-primary/70 text-xs">{item.project_name}</span>
                      </td>
                      <td className="px-4 py-3 text-xs text-text-primary/60 whitespace-nowrap">
                        <span>{item.archive_room}</span>
                        <span className="font-mono text-text-primary/40 ml-1">{item.archive_location_code}</span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">
                        {item.last_verified_at
                          ? format(new Date(item.last_verified_at), 'dd MMM yyyy')
                          : '—'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className={`font-mono text-xs ${overdue ? 'text-accent-critical' : 'text-text-primary/60'}`}>
                            {format(new Date(item.next_verification_at), 'dd MMM yyyy')}
                          </span>
                          {overdue && <Badge variant="critical">Overdue</Badge>}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
