'use client'

import { useMemo, useState } from 'react'
import { format, startOfMonth, endOfMonth, addMonths, isSameDay, parseISO } from 'date-fns'
import { ChevronLeft, ChevronRight, Plus, MapPin } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ModuleGuard } from '@/components/states/module-guard'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { CalendarEventDialog } from '@/components/calendar/calendar-event-dialog'
import { useMe } from '@/hooks/use-me'
import { useCalendarEvents } from '@/hooks/use-calendar'
import type { BadgeVariant, CalendarEvent, CalendarEventSource } from '@/types'

const SOURCE_VARIANT: Record<CalendarEventSource, BadgeVariant> = {
  CALENDAR_EVENT: 'info',
  TASK_DEADLINE: 'warning',
  LEAVE: 'pending',
  PHYSICAL_FILE_RETURN: 'critical',
}

const SOURCE_LABEL: Record<CalendarEventSource, string> = {
  CALENDAR_EVENT: 'Event',
  TASK_DEADLINE: 'Task Deadline',
  LEAVE: 'Leave',
  PHYSICAL_FILE_RETURN: 'File Return',
}

export default function CalendarPage() {
  const { data: user } = useMe()
  const canManage = (user?.isSuperUser || user?.permissions.includes('task.manage')) ?? false

  const [currentMonth, setCurrentMonth] = useState(() => startOfMonth(new Date()))
  const fromDate = format(currentMonth, 'yyyy-MM-dd')
  const toDate = format(endOfMonth(currentMonth), 'yyyy-MM-dd')

  const { data: events, isLoading, error, refetch } = useCalendarEvents({
    from_date: fromDate,
    to_date: toDate,
  })

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null)

  const groups = useMemo(() => {
    const sorted = [...(events ?? [])].sort(
      (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime()
    )
    const map = new Map<string, CalendarEvent[]>()
    for (const ev of sorted) {
      const key = format(parseISO(ev.starts_at), 'yyyy-MM-dd')
      const list = map.get(key) ?? []
      list.push(ev)
      map.set(key, list)
    }
    return Array.from(map.entries())
  }, [events])

  function openCreate() {
    setEditingEvent(null)
    setDialogOpen(true)
  }

  function openEdit(ev: CalendarEvent) {
    setEditingEvent(ev)
    setDialogOpen(true)
  }

  return (
    <AppShell>
      <PageHeader
        title="Calendar"
        subtitle="Shared"
        actions={
          canManage ? (
            <button
              type="button"
              onClick={openCreate}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans font-medium bg-accent-saffron text-surface-deep rounded-md hover:bg-accent-warning transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base"
            >
              <Plus size={13} aria-hidden="true" />
              New Event
            </button>
          ) : null
        }
      />

      <ContentArea>
        <ModuleGuard code="calendar">
        <div className="flex items-center justify-between mb-5">
          <button
            type="button"
            onClick={() => setCurrentMonth((m) => addMonths(m, -1))}
            aria-label="Previous month"
            className="p-1.5 rounded-md border border-surface-border text-text-primary/60 hover:text-text-primary hover:bg-surface-raised transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron"
          >
            <ChevronLeft size={16} aria-hidden="true" />
          </button>
          <h2 className="font-serif italic text-lg text-text-primary">
            {format(currentMonth, 'MMMM yyyy')}
          </h2>
          <button
            type="button"
            onClick={() => setCurrentMonth((m) => addMonths(m, 1))}
            aria-label="Next month"
            className="p-1.5 rounded-md border border-surface-border text-text-primary/60 hover:text-text-primary hover:bg-surface-raised transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron"
          >
            <ChevronRight size={16} aria-hidden="true" />
          </button>
        </div>

        {isLoading && <SkeletonScreen rows={6} />}

        {!isLoading && error && (
          <ErrorState
            message={error instanceof Error ? error.message : 'Failed to load calendar events'}
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && groups.length === 0 && (
          <EmptyState heading="No events this month" body="Events, deadlines, leave and file returns will appear here." />
        )}

        {!isLoading && !error && groups.length > 0 && (
          <div className="space-y-6">
            {groups.map(([dateKey, dayEvents]) => (
              <div key={dateKey}>
                <h3 className="text-xs font-sans uppercase tracking-wider text-text-primary/40 mb-2">
                  {format(parseISO(dateKey), 'EEEE, dd MMM yyyy')}
                  {isSameDay(parseISO(dateKey), new Date()) && (
                    <span className="ml-2 text-accent-saffron">Today</span>
                  )}
                </h3>
                <ul className="space-y-2">
                  {dayEvents.map((ev) => (
                    <li
                      key={ev.id}
                      className="flex items-start gap-3 rounded-lg border border-surface-border bg-surface-raised px-4 py-3"
                    >
                      <div className="flex-none font-mono text-xs text-text-primary/50 pt-0.5 w-12">
                        {format(parseISO(ev.starts_at), 'HH:mm')}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-sans text-text-primary">{ev.title}</p>
                          <Badge variant={SOURCE_VARIANT[ev.source]}>{SOURCE_LABEL[ev.source]}</Badge>
                        </div>
                        {ev.description && (
                          <p className="text-xs font-sans text-text-primary/50 mt-0.5">{ev.description}</p>
                        )}
                        {ev.location && (
                          <p className="flex items-center gap-1 text-xs font-sans text-text-primary/40 mt-1">
                            <MapPin size={11} aria-hidden="true" />
                            {ev.location}
                          </p>
                        )}
                      </div>
                      {canManage && ev.source === 'CALENDAR_EVENT' && (
                        <button
                          type="button"
                          onClick={() => openEdit(ev)}
                          className="flex-none text-xs font-sans text-accent-saffron/70 hover:text-accent-saffron transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron rounded"
                        >
                          Edit
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
        </ModuleGuard>
      </ContentArea>

      <CalendarEventDialog
        open={dialogOpen}
        event={editingEvent}
        onClose={() => setDialogOpen(false)}
      />
    </AppShell>
  )
}
