import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchCalendarEvents, createCalendarEvent, updateCalendarEvent } from '@/lib/api'
import type { CreateCalendarEventPayload, UpdateCalendarEventPayload } from '@/types'

export const CALENDAR_EVENTS_KEY = ['calendar', 'events'] as const

export function useCalendarEvents(params?: {
  from_date?: string
  to_date?: string
  project_id?: string
}) {
  return useQuery({
    queryKey: [...CALENDAR_EVENTS_KEY, params],
    queryFn: () => fetchCalendarEvents(params),
    staleTime: 30 * 1000,
  })
}

export function useCreateCalendarEvent() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateCalendarEventPayload) => createCalendarEvent(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: CALENDAR_EVENTS_KEY })
    },
  })
}

export function useUpdateCalendarEvent(eventId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateCalendarEventPayload) => updateCalendarEvent(eventId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: CALENDAR_EVENTS_KEY })
    },
  })
}
