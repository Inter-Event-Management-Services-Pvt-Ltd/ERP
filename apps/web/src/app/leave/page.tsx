'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { Plus, Check, X as XIcon, Loader2 } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { ModuleGuard } from '@/components/states/module-guard'
import { Badge } from '@/components/status/badge'
import { ConfirmDialog } from '@/components/status/confirm-dialog'
import { CreateLeaveDialog } from '@/components/leave/create-leave-dialog'
import { useMe } from '@/hooks/use-me'
import {
  useMyLeaveRequests,
  usePendingLeaveRequests,
  useApproveLeaveRequest,
  useRejectLeaveRequest,
  useCancelLeaveRequest,
} from '@/hooks/use-leave'
import { apiErrorMessage } from '@/lib/errors'
import type { BadgeVariant, LeaveRequest, LeaveStatus } from '@/types'

const STATUS_VARIANT: Record<LeaveStatus, BadgeVariant> = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  CANCELLED: 'archived',
}

function formatDate(iso: string): string {
  return format(new Date(iso), 'dd MMM yyyy')
}

function PendingReviewRow({ request }: { request: LeaveRequest }) {
  const { mutate: approve, isPending: approving } = useApproveLeaveRequest()
  const { mutate: reject, isPending: rejecting } = useRejectLeaveRequest()
  const [comment, setComment] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleApprove() {
    setError(null)
    approve(
      { requestId: request.id, payload: { review_comment: comment.trim() || undefined } },
      { onError: (err) => setError(apiErrorMessage(err)) }
    )
  }

  function handleReject() {
    setError(null)
    reject(
      { requestId: request.id, payload: { review_comment: comment.trim() || undefined } },
      { onError: (err) => setError(apiErrorMessage(err)) }
    )
  }

  const busy = approving || rejecting

  return (
    <tr className="border-b border-surface-border last:border-0 align-top">
      <td className="px-4 py-3 text-text-primary/80 whitespace-nowrap">
        {request.employee ? (
          <span>
            {request.employee.full_name}{' '}
            <span className="text-text-primary/40 font-mono text-xs">
              {request.employee.employee_code}
            </span>
          </span>
        ) : (
          '—'
        )}
      </td>
      <td className="px-4 py-3 text-text-primary/70 whitespace-nowrap">
        {request.leave_type?.name ?? '—'}
      </td>
      <td className="px-4 py-3 font-mono text-xs text-text-primary/70 whitespace-nowrap">
        {formatDate(request.start_date)} – {formatDate(request.end_date)}
      </td>
      <td className="px-4 py-3 text-sm text-text-primary/70 max-w-xs">{request.reason}</td>
      <td className="px-4 py-3 min-w-[12rem]">
        <input
          type="text"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Review comment (optional)"
          aria-label={`Review comment for ${request.employee?.full_name ?? 'leave request'}`}
          className="w-full rounded-md border border-surface-border bg-surface-base px-2 py-1.5 text-xs font-sans text-text-primary placeholder:text-text-primary/30 focus:outline-none focus:ring-2 focus:ring-accent-saffron"
        />
        {error && <p role="alert" className="mt-1 text-xs text-accent-critical">{error}</p>}
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleApprove}
            disabled={busy}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-sans font-medium rounded-md bg-accent-saffron text-surface-deep hover:bg-accent-warning disabled:opacity-40 transition-colors"
          >
            {approving ? <Loader2 size={12} className="animate-spin" aria-hidden="true" /> : <Check size={12} aria-hidden="true" />}
            Approve
          </button>
          <button
            type="button"
            onClick={handleReject}
            disabled={busy}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-sans font-medium rounded-md border border-surface-border text-accent-critical hover:bg-accent-madder/10 disabled:opacity-40 transition-colors"
          >
            {rejecting ? <Loader2 size={12} className="animate-spin" aria-hidden="true" /> : <XIcon size={12} aria-hidden="true" />}
            Reject
          </button>
        </div>
      </td>
    </tr>
  )
}

export default function LeavePage() {
  const { data: user } = useMe()
  const canReview = (user?.isSuperUser || user?.permissions.includes('leave.review')) ?? false

  const { data: myRequests, isLoading, error, refetch } = useMyLeaveRequests()
  const {
    data: pendingRequests,
    isLoading: pendingLoading,
    error: pendingError,
    refetch: refetchPending,
  } = usePendingLeaveRequests()

  const { mutate: cancelRequest, isPending: cancelling } = useCancelLeaveRequest()
  const [cancelTarget, setCancelTarget] = useState<LeaveRequest | null>(null)
  const [cancelError, setCancelError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  function handleCancel() {
    if (!cancelTarget) return
    setCancelError(null)
    cancelRequest(cancelTarget.id, {
      onSuccess: () => setCancelTarget(null),
      onError: (err) => setCancelError(apiErrorMessage(err)),
    })
  }

  return (
    <AppShell>
      <PageHeader
        title="Leave"
        subtitle="Requests"
        actions={
          <button
            type="button"
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans font-medium bg-accent-saffron text-surface-deep rounded-md hover:bg-accent-warning transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
          >
            <Plus size={13} aria-hidden="true" />
            New Request
          </button>
        }
      />

      <ContentArea>
        <ModuleGuard code="leave">
        {canReview && (
          <>
            <h2 className="font-serif italic text-lg text-text-primary mb-3">Pending Review</h2>

            {pendingLoading && <SkeletonScreen rows={3} />}

            {!pendingLoading && pendingError && (
              <ErrorState
                message={pendingError instanceof Error ? pendingError.message : 'Failed to load pending requests'}
                onRetry={() => refetchPending()}
              />
            )}

            {!pendingLoading && !pendingError && (pendingRequests ?? []).length === 0 && (
              <EmptyState heading="Nothing to review" body="There are no pending leave requests right now." />
            )}

            {!pendingLoading && !pendingError && (pendingRequests ?? []).length > 0 && (
              <div className="overflow-x-auto rounded-lg border border-surface-border mb-8">
                <table className="w-full text-sm font-sans">
                  <thead>
                    <tr className="border-b border-surface-border bg-surface-raised">
                      {['Employee', 'Type', 'Dates', 'Reason', 'Comment', 'Action'].map((h) => (
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
                    {(pendingRequests ?? []).map((r) => (
                      <PendingReviewRow key={r.id} request={r} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        <h2 className="font-serif italic text-lg text-text-primary mb-3">My Requests</h2>

        {isLoading && <SkeletonScreen rows={4} />}

        {!isLoading && error && (
          <ErrorState
            message={error instanceof Error ? error.message : 'Failed to load leave requests'}
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && (myRequests ?? []).length === 0 && (
          <EmptyState heading="No leave requests" body="Submit a new request to get started." />
        )}

        {!isLoading && !error && (myRequests ?? []).length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Type', 'Dates', 'Reason', 'Status', 'Review Comment', ''].map((h) => (
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
                {(myRequests ?? []).map((r) => (
                  <tr key={r.id} className="border-b border-surface-border last:border-0">
                    <td className="px-4 py-3 text-text-primary/80 whitespace-nowrap">
                      {r.leave_type?.name ?? '—'}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/70 whitespace-nowrap">
                      {formatDate(r.start_date)} – {formatDate(r.end_date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-text-primary/70 max-w-xs">{r.reason}</td>
                    <td className="px-4 py-3">
                      <Badge variant={STATUS_VARIANT[r.status]}>{r.status}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-text-primary/60 max-w-xs">
                      {r.review_comment ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {r.status === 'PENDING' && (
                        <button
                          type="button"
                          onClick={() => setCancelTarget(r)}
                          className="text-xs font-sans text-accent-critical hover:underline focus-visible:ring-2 focus-visible:ring-accent-saffron rounded"
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        </ModuleGuard>
      </ContentArea>

      <CreateLeaveDialog open={showCreate} onClose={() => setShowCreate(false)} />

      <ConfirmDialog
        open={!!cancelTarget}
        title="Cancel leave request?"
        description={
          cancelError ?? 'This will cancel your pending leave request. This action cannot be undone.'
        }
        confirmLabel={cancelling ? 'Cancelling…' : 'Cancel Request'}
        destructive
        onConfirm={handleCancel}
        onCancel={() => {
          setCancelTarget(null)
          setCancelError(null)
        }}
      />
    </AppShell>
  )
}
