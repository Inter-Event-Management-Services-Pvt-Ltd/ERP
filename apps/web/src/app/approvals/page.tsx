'use client'

import { useState } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { Plus, CheckCircle2 } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { ModuleGuard } from '@/components/states/module-guard'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { CreateApprovalDialog } from '@/components/approvals/create-approval-dialog'
import { useApprovals } from '@/hooks/use-approvals'
import type { ApprovalStatus, BadgeVariant } from '@/types'

const STATUS_TABS: Array<{ label: string; value: string }> = [
  { label: 'All', value: '' },
  { label: 'Pending', value: 'PENDING' },
  { label: 'Approved', value: 'APPROVED' },
  { label: 'Rejected', value: 'REJECTED' },
  { label: 'Revision Requested', value: 'REVISION_REQUESTED' },
  { label: 'Cancelled', value: 'CANCELLED' },
]

const STATUS_VARIANT: Record<ApprovalStatus, BadgeVariant> = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  REVISION_REQUESTED: 'warning',
  CANCELLED: 'archived',
}

const STATUS_LABEL: Record<ApprovalStatus, string> = {
  PENDING: 'Pending',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
  REVISION_REQUESTED: 'Revision',
  CANCELLED: 'Cancelled',
}

function targetLabel(a: {
  project_id: string | null
  document_version_id: string | null
  archive_export_id: string | null
  leave_request_id: string | null
}): string {
  if (a.project_id) return 'Project'
  if (a.document_version_id) return 'Document Version'
  if (a.archive_export_id) return 'Archive Export'
  if (a.leave_request_id) return 'Leave Request'
  return '—'
}

export default function ApprovalsPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const { data: approvals, isLoading, error, refetch } = useApprovals(
    statusFilter ? { status: statusFilter, limit: 100 } : { limit: 100 }
  )

  return (
    <AppShell>
      <PageHeader
        title="Approvals"
        subtitle="Request and review approvals"
        actions={
          <button
            type="button"
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors"
          >
            <Plus size={16} aria-hidden="true" />
            New Approval
          </button>
        }
      />

      <ContentArea>
        <ModuleGuard code="approvals">
        {/* Status filter tabs */}
        <div className="flex gap-1 mb-5 flex-wrap" role="group" aria-label="Filter by status">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => setStatusFilter(tab.value)}
              aria-pressed={statusFilter === tab.value}
              className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                statusFilter === tab.value
                  ? 'bg-accent-saffron/10 text-accent-saffron border border-accent-saffron/30'
                  : 'text-text-primary/50 hover:text-text-primary border border-transparent'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {isLoading && <SkeletonScreen rows={6} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && approvals?.length === 0 && (
          <EmptyState
            icon={CheckCircle2}
            heading="No approvals"
            body={statusFilter ? 'No approvals match the selected status.' : 'No approval requests yet.'}
          />
        )}

        {!isLoading && !error && approvals && approvals.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Type', 'Target', 'Requested by', 'Assigned to', 'Requested at', 'Status'].map((h) => (
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
                    className={`border-b border-surface-border last:border-0 hover:bg-surface-raised/50 transition-colors ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Link
                        href={`/approvals/${a.id}`}
                        className="font-medium text-text-primary/80 hover:text-accent-saffron transition-colors"
                      >
                        {a.approval_type?.name ?? a.approval_type_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-xs text-text-primary/50 font-mono">
                        {targetLabel(a)}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {a.requested_by_employee ? (
                        <span className="text-text-primary/70">
                          <span className="font-mono text-xs text-text-primary/40 mr-1.5">
                            {a.requested_by_employee.employee_code}
                          </span>
                          {a.requested_by_employee.full_name}
                        </span>
                      ) : (
                        <span className="text-text-primary/30">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-text-primary/70">
                      {a.assigned_to_employee?.full_name ?? (
                        <span className="text-text-primary/30">Unassigned</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">
                      {format(new Date(a.requested_at), 'dd MMM yyyy HH:mm')}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Badge variant={STATUS_VARIANT[a.status] ?? 'info'}>
                        {STATUS_LABEL[a.status] ?? a.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        </ModuleGuard>
      </ContentArea>

      {showCreate && <CreateApprovalDialog onClose={() => setShowCreate(false)} />}
    </AppShell>
  )
}
