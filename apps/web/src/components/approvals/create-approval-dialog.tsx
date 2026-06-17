'use client'

import { useState } from 'react'
import { useApprovalTypes, useCreateApproval } from '@/hooks/use-approvals'
import { useProjects } from '@/hooks/use-projects'
import { apiErrorMessage } from '@/lib/errors'

type TargetField = 'project_id' | 'document_version_id' | 'archive_export_id' | 'leave_request_id'

const TARGET_LABELS: Record<TargetField, string> = {
  project_id: 'Project',
  document_version_id: 'Document Version',
  archive_export_id: 'Archive Export',
  leave_request_id: 'Leave Request',
}

export function CreateApprovalDialog({ onClose }: { onClose: () => void }) {
  const { data: types } = useApprovalTypes()
  const { data: projects } = useProjects()
  const { mutateAsync, isPending, error } = useCreateApproval()

  const [approvalTypeId, setApprovalTypeId] = useState('')
  const [targetField, setTargetField] = useState<TargetField>('project_id')
  const [targetId, setTargetId] = useState('')
  const [assignedTo, setAssignedTo] = useState('')
  const [comment, setComment] = useState('')
  const [validationError, setValidationError] = useState('')

  function handleTargetTypeChange(field: TargetField) {
    setTargetField(field)
    setTargetId('')
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setValidationError('')

    if (!approvalTypeId) {
      setValidationError('Select an approval type.')
      return
    }
    if (!targetId.trim()) {
      setValidationError('A target is required. Select or enter the target ID.')
      return
    }

    try {
      await mutateAsync({
        approval_type_id: approvalTypeId,
        [targetField]: targetId.trim(),
        assigned_to: assignedTo.trim() || null,
        comment: comment.trim() || undefined,
      })
      onClose()
    } catch {
      // error rendered below from mutation state
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="New Approval Request"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-lg bg-surface-base border border-surface-border rounded-xl shadow-xl p-6 flex flex-col gap-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-semibold text-text-primary">New Approval Request</h2>

        {/* Approval type */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="approval-type" className="text-xs font-semibold text-text-primary/60 uppercase tracking-wide">
            Approval type <span aria-hidden="true">*</span>
          </label>
          <select
            id="approval-type"
            value={approvalTypeId}
            onChange={(e) => setApprovalTypeId(e.target.value)}
            className="h-9 px-3 text-sm bg-surface-raised border border-surface-border rounded-md text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-saffron/50"
          >
            <option value="">Select type…</option>
            {types?.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>

        {/* Target type selector */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-semibold text-text-primary/60 uppercase tracking-wide">
            Target <span aria-hidden="true">*</span>
          </span>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Target type">
            {(Object.keys(TARGET_LABELS) as TargetField[]).map((field) => (
              <button
                key={field}
                type="button"
                onClick={() => handleTargetTypeChange(field)}
                className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                  targetField === field
                    ? 'bg-accent-saffron/10 border-accent-saffron/40 text-accent-saffron'
                    : 'bg-surface-raised border-surface-border text-text-primary/50 hover:text-text-primary hover:border-surface-border'
                }`}
              >
                {TARGET_LABELS[field]}
              </button>
            ))}
          </div>

          {targetField === 'project_id' ? (
            <select
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              aria-label="Select project"
              className="h-9 px-3 text-sm bg-surface-raised border border-surface-border rounded-md text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-saffron/50"
            >
              <option value="">Select project…</option>
              {projects?.map((p) => (
                <option key={p.id} value={p.id}>{p.project_code} — {p.name}</option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              placeholder={`${TARGET_LABELS[targetField]} ID (UUID)…`}
              aria-label={`${TARGET_LABELS[targetField]} ID`}
              className="h-9 px-3 text-sm font-mono bg-surface-raised border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50"
            />
          )}
        </div>

        {/* Assigned to (optional) */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="assigned-to" className="text-xs font-semibold text-text-primary/60 uppercase tracking-wide">
            Assign to <span className="font-normal normal-case text-text-primary/30">(employee UUID, optional)</span>
          </label>
          <input
            id="assigned-to"
            type="text"
            value={assignedTo}
            onChange={(e) => setAssignedTo(e.target.value)}
            placeholder="Employee UUID…"
            className="h-9 px-3 text-sm font-mono bg-surface-raised border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50"
          />
        </div>

        {/* Comment */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="approval-comment" className="text-xs font-semibold text-text-primary/60 uppercase tracking-wide">
            Comment <span className="font-normal normal-case text-text-primary/30">(optional)</span>
          </label>
          <textarea
            id="approval-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
            placeholder="Describe the request…"
            className="px-3 py-2 text-sm bg-surface-raised border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50 resize-none"
          />
        </div>

        {(validationError || error) && (
          <p role="alert" className="text-xs text-accent-critical">
            {validationError || apiErrorMessage(error)}
          </p>
        )}

        <div className="flex justify-end gap-3 pt-1">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-text-primary/60 hover:text-text-primary transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="px-4 py-2 text-sm font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50"
          >
            {isPending ? 'Submitting…' : 'Submit Request'}
          </button>
        </div>
      </form>
    </div>
  )
}
