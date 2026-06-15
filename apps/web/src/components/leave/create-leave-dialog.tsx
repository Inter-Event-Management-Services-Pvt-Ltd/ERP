'use client'

import { useEffect, useRef, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { FormField, inputCls } from '@/components/ui/form-field'
import { useLeaveTypes } from '@/hooks/use-lookups'
import { useCreateLeaveRequest } from '@/hooks/use-leave'
import { apiErrorMessage } from '@/lib/errors'

interface CreateLeaveDialogProps {
  open: boolean
  onClose: () => void
}

export function CreateLeaveDialog({ open, onClose }: CreateLeaveDialogProps) {
  const { data: leaveTypes = [] } = useLeaveTypes()
  const { mutate, isPending } = useCreateLeaveRequest()
  const cancelRef = useRef<HTMLButtonElement>(null)

  const [leaveTypeId, setLeaveTypeId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setLeaveTypeId('')
      setStartDate('')
      setEndDate('')
      setReason('')
      setError(null)
      cancelRef.current?.focus()
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!leaveTypeId || !startDate || !endDate || !reason.trim()) {
      setError('All fields are required.')
      return
    }
    if (endDate < startDate) {
      setError('End date must be on or after the start date.')
      return
    }
    setError(null)
    mutate(
      {
        leave_type_id: leaveTypeId,
        start_date: startDate,
        end_date: endDate,
        reason: reason.trim(),
      },
      {
        onSuccess: () => onClose(),
        onError: (err) => setError(apiErrorMessage(err)),
      }
    )
  }

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="leave-dialog-title" className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} aria-hidden="true" />
      <form
        onSubmit={handleSubmit}
        className="relative bg-surface-raised border border-surface-border rounded-lg p-6 max-w-md w-full mx-4 animate-scale-in space-y-4"
      >
        <h2 id="leave-dialog-title" className="font-serif italic text-lg text-text-primary">
          New Leave Request
        </h2>

        <FormField label="Leave type" htmlFor="leave-type" required>
          <select
            id="leave-type"
            value={leaveTypeId}
            onChange={(e) => setLeaveTypeId(e.target.value)}
            required
            aria-required="true"
            className={inputCls}
          >
            <option value="">Select leave type…</option>
            {leaveTypes.map((lt) => (
              <option key={lt.id} value={lt.id}>
                {lt.name}
              </option>
            ))}
          </select>
        </FormField>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Start date" htmlFor="leave-start" required>
            <input
              id="leave-start"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
              aria-required="true"
              className={inputCls}
            />
          </FormField>
          <FormField label="End date" htmlFor="leave-end" required>
            <input
              id="leave-end"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              required
              aria-required="true"
              className={inputCls}
            />
          </FormField>
        </div>

        <FormField label="Reason" htmlFor="leave-reason" required error={error ?? undefined}>
          <textarea
            id="leave-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            required
            aria-required="true"
            className={inputCls}
          />
        </FormField>

        <div className="flex gap-3 justify-end">
          <button
            ref={cancelRef}
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-sans rounded-md border border-surface-border text-text-primary/70 hover:text-text-primary hover:bg-surface-base transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-sans font-medium rounded-md bg-accent-saffron text-surface-deep hover:bg-accent-warning disabled:opacity-40 transition-colors"
          >
            {isPending && <Loader2 size={14} className="animate-spin" aria-hidden="true" />}
            Submit Request
          </button>
        </div>
      </form>
    </div>
  )
}
