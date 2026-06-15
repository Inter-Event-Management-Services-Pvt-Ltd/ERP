'use client'

import { useMemo, useState } from 'react'
import { format } from 'date-fns'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { SearchInput } from '@/components/ui/search-input'
import { useDirectorAttendance } from '@/hooks/use-attendance'
import type { BadgeVariant } from '@/types'

const STATE_VARIANT: Record<string, BadgeVariant> = {
  PRESENT: 'approved',
  CHECKED_IN: 'active',
  CHECKED_OUT: 'info',
  ABSENT: 'critical',
  ON_LEAVE: 'pending',
}

function formatDuration(minutes: number | null): string {
  if (minutes == null) return '—'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${h}h ${m}m`
}

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  return format(new Date(iso), 'HH:mm')
}

export default function DirectorAttendancePage() {
  const { data: summaries, isLoading, error, refetch } = useDirectorAttendance()
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    if (!summaries) return []
    const q = search.toLowerCase()
    return summaries.filter(
      (s) => !q || s.full_name.toLowerCase().includes(q) || s.employee_code.toLowerCase().includes(q)
    )
  }, [summaries, search])

  return (
    <AppShell>
      <PageHeader
        title="Attendance"
        subtitle={`Company-wide · ${format(new Date(), 'dd MMM yyyy')}`}
      />

      <ContentArea>
        <div className="mb-5">
          <SearchInput value={search} onChange={setSearch} placeholder="Search employee…" className="w-64" />
        </div>

        {isLoading && <SkeletonScreen rows={8} />}

        {!isLoading && error && (
          <ErrorState
            message={error instanceof Error ? error.message : 'Failed to load attendance summary'}
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && filtered.length === 0 && (
          <EmptyState
            heading={search ? 'No matching employees' : 'No attendance records today'}
            body={search ? 'Try adjusting your search.' : 'Attendance records will appear here once employees check in.'}
          />
        )}

        {!isLoading && !error && filtered.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Employee', 'First Check-in', 'Last Check-out', 'Total Time', 'Status'].map((h) => (
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
                {filtered.map((s, i) => (
                  <tr
                    key={s.employee_id}
                    className={`border-b border-surface-border last:border-0 ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 text-text-primary whitespace-nowrap">
                      {s.full_name}{' '}
                      <span className="text-text-primary/40 font-mono text-xs">{s.employee_code}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/70 whitespace-nowrap">
                      {formatTime(s.first_check_in)}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/70 whitespace-nowrap">
                      {formatTime(s.last_check_out)}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/70 whitespace-nowrap">
                      {formatDuration(s.total_minutes)}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={STATE_VARIANT[s.attendance_state] ?? 'info'}>
                        {s.attendance_state.replace(/_/g, ' ')}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
