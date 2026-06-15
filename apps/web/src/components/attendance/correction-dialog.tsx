'use client'

import { useEffect, useRef, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { FormField, inputCls } from '@/components/ui/form-field'
import { useCorrectAttendanceSession } from '@/hooks/use-attendance'
import { apiErrorMessage } from '@/lib/errors'
import type { AttendanceSession } from '@/types'

interface CorrectionDialogProps {
  session: AttendanceSession | null
  onClose: () => void
}

/** Converts an ISO timestamp to the value expected by <input type="datetime-local">. */
function toLocalInputValue(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function CorrectionDialog({ session, onClose }: CorrectionDialogProps) {
  const { mutate, isPending } = useCorrectAttendanceSession()
  const cancelRef = useRef<HTMLButtonElement>(null)

  const [checkedInAt, setCheckedInAt] = useState('')
  const [checkedOutAt, setCheckedOutAt] = useState('')
  const [remarks, setRemarks] = useState('')
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (session) {
      setCheckedInAt(toLocalInputValue(session.checked_in_at))
      setCheckedOutAt(toLocalInputValue(session.checked_out_at))
      setRemarks(session.remarks ?? '')
      setReason('')
      setError(null)
    }
  }, [session])

  useEffect(() => {
    if (session) cancelRef.current?.focus()
  }, [session])

  useEffect(() => {
    if (!session) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [session, onClose])

  if (!session) return null

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!session) return
    if (!reason.trim()) {
      setError('Correction reason is required.')
      return
    }
    setError(null)
    mutate(
      {
        sessionId: session.id,
        payload: {
          checked_in_at: checkedInAt ? new Date(checkedInAt).toISOString() : undefined,
          checked_out_at: checkedOutAt ? new Date(checkedOutAt).toISOString() : undefined,
          remarks: remarks.trim() ? remarks.trim() : undefined,
          correction_reason: reason.trim(),
        },
      },
      {
        onSuccess: () => onClose(),
        onError: (err) => setError(apiErrorMessage(err)),
      }
    )
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="correction-title"
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      <div className="absolute inset-0 bg-black/60" onClick={onClose} aria-hidden="true" />
      <form
        onSubmit={handleSubmit}
        className="relative bg-surface-raised border border-surface-border rounded-lg p-6 max-w-md w-full mx-4 animate-scale-in space-y-4"
      >
        <h2 id="correction-title" className="font-serif italic text-lg text-text-primary">
          Correct Attendance Session
        </h2>

        <FormField label="Checked in at" htmlFor="correction-in">
          <input
            id="correction-in"
            type="datetime-local"
            value={checkedInAt}
            onChange={(e) => setCheckedInAt(e.target.value)}
            className={inputCls}
          />
        </FormField>

        <FormField label="Checked out at" htmlFor="correction-out">
          <input
            id="correction-out"
            type="datetime-local"
            value={checkedOutAt}
            onChange={(e) => setCheckedOutAt(e.target.value)}
            className={inputCls}
          />
        </FormField>

        <FormField label="Remarks" htmlFor="correction-remarks">
          <input
            id="correction-remarks"
            type="text"
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            className={inputCls}
          />
        </FormField>

        <FormField label="Correction reason" htmlFor="correction-reason" required error={error ?? undefined}>
          <textarea
            id="correction-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={2}
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
            Save Correction
          </button>
        </div>
      </form>
    </div>
  )
}
