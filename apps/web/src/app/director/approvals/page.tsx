'use client'

import { format } from 'date-fns'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { useDirectorApprovals } from '@/hooks/use-director'

function formatApprovalType(raw: string): string {
  return raw.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
}

export default function DirectorApprovalsPage() {
  const { data: approvals, isLoading, error, refetch } = useDirectorApprovals({ limit: 100 })

  return (
    <AppShell>
      <PageHeader title="Approvals" subtitle="Pending queue" />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={6} />}

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

        {!isLoading && !error && approvals?.length === 0 && (
          <EmptyState
            heading="No pending approvals"
            body="When approval requests are raised, they will appear here."
          />
        )}

        {!isLoading && !error && approvals && approvals.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs text-text-primary/40 font-sans">
              Approval actions are not yet available. This is a read-only queue view.
            </p>

            <div className="overflow-x-auto rounded-lg border border-surface-border">
              <table className="w-full text-sm font-sans">
                <thead>
                  <tr className="border-b border-surface-border bg-surface-raised">
                    {['Type', 'Project', 'Requested by', 'Assigned to', 'Requested at', 'Status'].map((h) => (
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
                  {approvals.map((a, i) => (
                    <tr
                      key={a.id}
                      className={`border-b border-surface-border last:border-0 ${
                        i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                      }`}
                    >
                      <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
                        {formatApprovalType(a.approval_type)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="font-mono text-xs text-text-primary/50 mr-1.5">{a.project_code}</span>
                        <span className="text-text-primary/80">{a.project_name}</span>
                      </td>
                      <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
                        {a.requested_by_name}
                      </td>
                      <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
                        {a.assigned_to_name}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">
                        {format(new Date(a.requested_at), 'dd MMM yyyy HH:mm')}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="pending">{a.status}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
