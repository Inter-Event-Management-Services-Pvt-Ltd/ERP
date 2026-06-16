'use client'

import { useState } from 'react'
import { use } from 'react'
import { format } from 'date-fns'
import { ArrowLeft, CheckCircle2, XCircle, RotateCcw } from 'lucide-react'
import Link from 'next/link'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { useApproval, useApproveApproval, useRejectApproval, useRequestRevision } from '@/hooks/use-approvals'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import type { ApprovalStatus, BadgeVariant } from '@/types'

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
  REVISION_REQUESTED: 'Revision Requested',
  CANCELLED: 'Cancelled',
}

function targetDisplay(a: {
  project_id: string | null
  document_version_id: string | null
  archive_export_id: string | null
  leave_request_id: string | null
}): { label: string; value: string } {
  if (a.project_id) return { label: 'Project', value: a.project_id }
  if (a.document_version_id) return { label: 'Document Version', value: a.document_version_id }
  if (a.archive_export_id) return { label: 'Archive Export', value: a.archive_export_id }
  if (a.leave_request_id) return { label: 'Leave Request', value: a.leave_request_id }
  return { label: '—', value: '' }
}

const ACTION_LABEL: Record<string, string> = {
  SUBMITTED: 'Submitted',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
  REVISION_REQUESTED: 'Revision Requested',
  CANCELLED: 'Cancelled',
}

const ACTION_COLOR: Record<string, string> = {
  SUBMITTED: 'text-text-primary/50',
  APPROVED: 'text-accent-saffron',
  REJECTED: 'text-accent-critical',
  REVISION_REQUESTED: 'text-accent-warning',
  CANCELLED: 'text-text-primary/30',
}

type ActionType = 'approve' | 'reject' | 'revision'

export default function ApprovalDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const { data: user } = useMe()
  const { data: approval, isLoading, error, refetch } = useApproval(id)

  const approveMutation = useApproveApproval()
  const rejectMutation = useRejectApproval()
  const revisionMutation = useRequestRevision()

  const [activeAction, setActiveAction] = useState<ActionType | null>(null)
  const [comment, setComment] = useState('')
  const [actionError, setActionError] = useState('')

  const canReview =
    (user?.isSuperUser ?? false) || (user?.permissions.includes('approval.approve') ?? false)

  const isPending = approval?.status === 'PENDING'
  const showActions = canReview && isPending

  const currentMutation =
    activeAction === 'approve' ? approveMutation :
    activeAction === 'reject' ? rejectMutation :
    activeAction === 'revision' ? revisionMutation : null

  async function handleActionSubmit(e: React.FormEvent) {
    e.preventDefault()
    setActionError('')

    if (activeAction === 'revision' && !comment.trim()) {
      setActionError('A comment is required when requesting revision.')
      return
    }

    const payload = { comment: comment.trim() || undefined }

    try {
      if (activeAction === 'approve') {
        await approveMutation.mutateAsync({ id, payload })
      } else if (activeAction === 'reject') {
        await rejectMutation.mutateAsync({ id, payload })
      } else if (activeAction === 'revision') {
        await revisionMutation.mutateAsync({ id, payload })
      }
      setActiveAction(null)
      setComment('')
    } catch (err) {
      setActionError(apiErrorMessage(err))
    }
  }

  function openAction(action: ActionType) {
    setActiveAction(action)
    setComment('')
    setActionError('')
  }

  if (isLoading) {
    return (
      <AppShell>
        <PageHeader title="Approval" subtitle="Loading…" />
        <ContentArea>
          <SkeletonScreen rows={6} />
        </ContentArea>
      </AppShell>
    )
  }

  if (error || !approval) {
    return (
      <AppShell>
        <PageHeader title="Approval" subtitle="Not found" />
        <ContentArea>
          <ErrorState
            message={error ? (error as Error).message : 'Approval not found.'}
            onRetry={() => refetch()}
          />
        </ContentArea>
      </AppShell>
    )
  }

  const target = targetDisplay(approval)
  const isTerminal = approval.status !== 'PENDING'

  return (
    <AppShell>
      <PageHeader
        title={approval.approval_type?.name ?? 'Approval'}
        subtitle={
          <div className="flex items-center gap-2 mt-0.5">
            <Link
              href="/approvals"
              className="font-mono text-xs text-accent-saffron/60 hover:text-accent-saffron transition-colors uppercase tracking-wide"
            >
              ← Approvals
            </Link>
          </div>
        }
      />

      <ContentArea>
        <div className="max-w-2xl flex flex-col gap-6">

          {/* Status + metadata card */}
          <section className="rounded-lg border border-surface-border bg-surface-raised p-5 flex flex-col gap-4">
            <div className="flex items-start justify-between gap-4">
              <h2 className="text-sm font-semibold text-text-primary">
                {approval.approval_type?.name ?? approval.approval_type_id}
              </h2>
              <Badge variant={STATUS_VARIANT[approval.status] ?? 'info'}>
                {STATUS_LABEL[approval.status] ?? approval.status}
              </Badge>
            </div>

            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
              <div>
                <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Target type</dt>
                <dd className="text-text-primary/80">{target.label}</dd>
              </div>
              {target.value && (
                <div>
                  <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Target ID</dt>
                  <dd className="font-mono text-xs text-text-primary/50 break-all">{target.value}</dd>
                </div>
              )}
              <div>
                <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Requested by</dt>
                <dd className="text-text-primary/80">
                  {approval.requested_by_employee ? (
                    <>
                      <span className="font-mono text-xs text-text-primary/40 mr-1.5">
                        {approval.requested_by_employee.employee_code}
                      </span>
                      {approval.requested_by_employee.full_name}
                    </>
                  ) : (
                    <span className="text-text-primary/30">—</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Assigned to</dt>
                <dd className="text-text-primary/80">
                  {approval.assigned_to_employee ? (
                    <>
                      <span className="font-mono text-xs text-text-primary/40 mr-1.5">
                        {approval.assigned_to_employee.employee_code}
                      </span>
                      {approval.assigned_to_employee.full_name}
                    </>
                  ) : (
                    <span className="text-text-primary/30">Unassigned</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Requested at</dt>
                <dd className="font-mono text-xs text-text-primary/60">
                  {format(new Date(approval.requested_at), 'dd MMM yyyy HH:mm')}
                </dd>
              </div>
              {approval.completed_at && (
                <div>
                  <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Completed at</dt>
                  <dd className="font-mono text-xs text-text-primary/60">
                    {format(new Date(approval.completed_at), 'dd MMM yyyy HH:mm')}
                  </dd>
                </div>
              )}
            </dl>
          </section>

          {/* Action history */}
          <section>
            <h2 className="text-xs font-semibold text-text-primary/40 uppercase tracking-widest mb-3">
              Action History
            </h2>
            {approval.actions.length === 0 ? (
              <p className="text-sm text-text-primary/40">No actions recorded yet.</p>
            ) : (
              <ol className="flex flex-col gap-0">
                {approval.actions.map((action, idx) => (
                  <li key={action.id} className="flex gap-3">
                    {/* Timeline line */}
                    <div className="flex flex-col items-center">
                      <div className="w-2.5 h-2.5 rounded-full bg-surface-border border-2 border-surface-deep mt-1 flex-none" />
                      {idx < approval.actions.length - 1 && (
                        <div className="w-px flex-1 bg-surface-border mt-1" />
                      )}
                    </div>

                    <div className="pb-5 flex-1 min-w-0">
                      <div className="flex items-baseline gap-2 flex-wrap">
                        <span className={`text-xs font-semibold font-mono uppercase tracking-wide ${ACTION_COLOR[action.action] ?? 'text-text-primary/50'}`}>
                          {ACTION_LABEL[action.action] ?? action.action}
                        </span>
                        <span className="text-xs text-text-primary/40 font-mono">
                          {format(new Date(action.created_at), 'dd MMM yyyy HH:mm')}
                        </span>
                      </div>
                      {action.performed_by_employee && (
                        <p className="text-xs text-text-primary/60 mt-0.5">
                          <span className="font-mono text-text-primary/40 mr-1">
                            {action.performed_by_employee.employee_code}
                          </span>
                          {action.performed_by_employee.full_name}
                        </p>
                      )}
                      {action.comment && (
                        <p className="text-sm text-text-primary/70 mt-1.5 bg-surface-raised border border-surface-border rounded-md px-3 py-2">
                          {action.comment}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>

          {/* Review actions */}
          {showActions && !activeAction && (
            <section>
              <h2 className="text-xs font-semibold text-text-primary/40 uppercase tracking-widest mb-3">
                Review
              </h2>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => openAction('approve')}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors"
                >
                  <CheckCircle2 size={15} aria-hidden="true" />
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => openAction('reject')}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-madder/10 border border-accent-madder/30 text-accent-critical rounded-lg hover:bg-accent-madder/20 transition-colors"
                >
                  <XCircle size={15} aria-hidden="true" />
                  Reject
                </button>
                <button
                  type="button"
                  onClick={() => openAction('revision')}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-warning/10 border border-accent-warning/30 text-accent-warning rounded-lg hover:bg-accent-warning/20 transition-colors"
                >
                  <RotateCcw size={15} aria-hidden="true" />
                  Request Revision
                </button>
              </div>
            </section>
          )}

          {/* Inline action form */}
          {showActions && activeAction && (
            <section>
              <h2 className="text-xs font-semibold text-text-primary/40 uppercase tracking-widest mb-3">
                {activeAction === 'approve' ? 'Confirm Approval' :
                 activeAction === 'reject' ? 'Confirm Rejection' :
                 'Request Revision'}
              </h2>
              <form onSubmit={handleActionSubmit} className="flex flex-col gap-3 rounded-lg border border-surface-border bg-surface-raised p-4">
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="action-comment" className="text-xs font-semibold text-text-primary/60 uppercase tracking-wide">
                    Comment
                    {activeAction === 'revision' ? (
                      <span className="text-accent-critical ml-1" aria-label="required">*</span>
                    ) : (
                      <span className="font-normal normal-case text-text-primary/30 ml-1">(optional)</span>
                    )}
                  </label>
                  <textarea
                    id="action-comment"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    rows={3}
                    placeholder={
                      activeAction === 'revision'
                        ? 'Describe what needs to be revised…'
                        : 'Add a comment (optional)…'
                    }
                    className="px-3 py-2 text-sm bg-surface-base border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50 resize-none"
                  />
                </div>

                {actionError && (
                  <p role="alert" className="text-xs text-accent-critical">
                    {actionError}
                  </p>
                )}

                <div className="flex gap-3 pt-1">
                  <button
                    type="submit"
                    disabled={currentMutation?.isPending ?? false}
                    className={`px-4 py-2 text-sm font-medium rounded-lg border transition-colors disabled:opacity-50 ${
                      activeAction === 'approve'
                        ? 'bg-accent-saffron/10 border-accent-saffron/30 text-accent-saffron hover:bg-accent-saffron/20'
                        : activeAction === 'reject'
                        ? 'bg-accent-madder/10 border-accent-madder/30 text-accent-critical hover:bg-accent-madder/20'
                        : 'bg-accent-warning/10 border-accent-warning/30 text-accent-warning hover:bg-accent-warning/20'
                    }`}
                  >
                    {currentMutation?.isPending ? 'Submitting…' :
                     activeAction === 'approve' ? 'Confirm Approval' :
                     activeAction === 'reject' ? 'Confirm Rejection' :
                     'Send Revision Request'}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setActiveAction(null); setComment(''); setActionError('') }}
                    className="px-4 py-2 text-sm text-text-primary/60 hover:text-text-primary transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </section>
          )}

          {/* Completed notice for non-reviewers on terminal approvals */}
          {isTerminal && !showActions && (
            <p className="text-xs text-text-primary/40 font-mono uppercase tracking-wide">
              This approval is {STATUS_LABEL[approval.status]?.toLowerCase()}.
            </p>
          )}

        </div>
      </ContentArea>
    </AppShell>
  )
}
