'use client'

import { format } from 'date-fns'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { Archive } from 'lucide-react'
import { useDirectorPhysicalFiles } from '@/hooks/use-director'

export default function DirectorArchivePage() {
  const { data: files, isLoading, error, refetch } = useDirectorPhysicalFiles({ limit: 100 })

  return (
    <AppShell>
      <PageHeader title="Physical Archive" subtitle="Checked-out files" />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={5} />}

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

        {!isLoading && !error && files?.length === 0 && (
          <EmptyState
            icon={Archive}
            heading="No checked-out files"
            body="All physical files are currently in the archive."
          />
        )}

        {!isLoading && !error && files && files.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['File code', 'Project', 'Client', 'Location', 'Checked out by', 'Checked out at', 'Expected return', 'Return status'].map((h) => (
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
                {files.map((f, i) => (
                  <tr
                    key={f.id}
                    className={`border-b border-surface-border last:border-0 ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/60 whitespace-nowrap">
                      {f.physical_file_code}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono text-xs text-text-primary/50 mr-1.5">{f.project_code}</span>
                      <span className="text-text-primary/80">{f.project_name}</span>
                    </td>
                    <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">{f.client_name}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono text-xs text-text-primary/50">{f.archive_room}</span>
                      {f.archive_location_code && (
                        <span className="font-mono text-xs text-text-primary/40 ml-1.5">{f.archive_location_code}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">{f.checked_out_by}</td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">
                      {format(new Date(f.checked_out_at), 'dd MMM HH:mm')}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">
                      {f.expected_return_at
                        ? format(new Date(f.expected_return_at), 'dd MMM yyyy')
                        : '—'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {f.is_return_overdue ? (
                        <Badge variant="overdue">Overdue</Badge>
                      ) : (
                        <Badge variant="active">On time</Badge>
                      )}
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
