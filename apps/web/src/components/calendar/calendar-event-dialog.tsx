'use client'

import { useEffect, useRef, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { FormField, inputCls } from '@/components/ui/form-field'
import { useProjects } from '@/hooks/use-projects'
import { useCreateCalendarEvent, useUpdateCalendarEvent } from '@/hooks/use-calendar'
import { apiErrorMessage } from '@/lib/errors'
import type { CalendarEvent, CalendarEventType } from '@/types'

const EVENT_TYPES: CalendarEventType[] = [
  'MEETING',
  'SITE_VISIT',
  'EVENT',
  'DEADLINE',
  'REMINDER',
]

function toLocalInputValue(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

interface CalendarEventDialogProps {
  open: boolean
  event?: CalendarEvent | null
  onClose: () => void
}

export function CalendarEventDialog({ open, event, onClose }: CalendarEventDialogProps) {
  const isEdit = !!event
  const { data: projects = [] } = useProjects()
  const { mutate: create, isPending: creating } = useCreateCalendarEvent()
  const { mutate: update, isPending: updating } = useUpdateCalendarEvent(event?.id ?? '')
  const cancelRef = useRef<HTMLButtonElement>(null)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [eventType, setEventType] = useState<CalendarEventType>('MEETING')
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')
  const [location, setLocation] = useState('')
  const [projectId, setProjectId] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setTitle(event?.title ?? '')
      setDescription(event?.description ?? '')
      setEventType(event?.event_type ?? 'MEETING')
      setStartsAt(toLocalInputValue(event?.starts_at ?? null))
      setEndsAt(toLocalInputValue(event?.ends_at ?? null))
      setLocation(event?.location ?? '')
      setProjectId(event?.project_id ?? '')
      setError(null)
      cancelRef.current?.focus()
    }
  }, [open, event])

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
    if (!title.trim() || !startsAt) {
      setError('Title and start time are required.')
      return
    }
    setError(null)

    if (isEdit) {
      update(
        {
          title: title.trim(),
          description: description.trim() || undefined,
          starts_at: new Date(startsAt).toISOString(),
          ends_at: endsAt ? new Date(endsAt).toISOString() : undefined,
          location: location.trim() || undefined,
        },
        {
          onSuccess: () => onClose(),
          onError: (err) => setError(apiErrorMessage(err)),
        }
      )
    } else {
      create(
        {
          event_type: eventType,
          title: title.trim(),
          description: description.trim() || undefined,
          starts_at: new Date(startsAt).toISOString(),
          ends_at: endsAt ? new Date(endsAt).toISOString() : undefined,
          location: location.trim() || undefined,
          project_id: projectId || undefined,
        },
        {
          onSuccess: () => onClose(),
          onError: (err) => setError(apiErrorMessage(err)),
        }
      )
    }
  }

  const isPending = creating || updating

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="calendar-dialog-title" className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} aria-hidden="true" />
      <form
        onSubmit={handleSubmit}
        className="relative bg-surface-raised border border-surface-border rounded-lg p-6 max-w-lg w-full mx-4 animate-scale-in space-y-4 max-h-[90vh] overflow-y-auto"
      >
        <h2 id="calendar-dialog-title" className="font-serif italic text-lg text-text-primary">
          {isEdit ? 'Edit Event' : 'New Event'}
        </h2>

        <FormField label="Title" htmlFor="event-title" required>
          <input
            id="event-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            aria-required="true"
            className={inputCls}
          />
        </FormField>

        <FormField label="Description" htmlFor="event-description">
          <textarea
            id="event-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className={inputCls}
          />
        </FormField>

        {!isEdit && (
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Event type" htmlFor="event-type" required>
              <select
                id="event-type"
                value={eventType}
                onChange={(e) => setEventType(e.target.value as CalendarEventType)}
                required
                aria-required="true"
                className={inputCls}
              >
                {EVENT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.replace('_', ' ')}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField label="Project" htmlFor="event-project">
              <select
                id="event-project"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                className={inputCls}
              >
                <option value="">None</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </FormField>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Starts at" htmlFor="event-starts" required>
            <input
              id="event-starts"
              type="datetime-local"
              value={startsAt}
              onChange={(e) => setStartsAt(e.target.value)}
              required
              aria-required="true"
              className={inputCls}
            />
          </FormField>
          <FormField label="Ends at" htmlFor="event-ends">
            <input
              id="event-ends"
              type="datetime-local"
              value={endsAt}
              onChange={(e) => setEndsAt(e.target.value)}
              className={inputCls}
            />
          </FormField>
        </div>

        <FormField label="Location" htmlFor="event-location" error={error ?? undefined}>
          <input
            id="event-location"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
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
            {isEdit ? 'Save Changes' : 'Create Event'}
          </button>
        </div>
      </form>
    </div>
  )
}
