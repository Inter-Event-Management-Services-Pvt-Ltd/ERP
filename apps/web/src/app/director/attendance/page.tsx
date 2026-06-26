'use client'

import { format } from 'date-fns'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { ModuleDisabledState } from '@/components/states/module-disabled-state'
import { useDirectorAttendance } from '@/hooks/use-attendance'
import { useModuleEnabled } from '@/hooks/use-modules'
import { apiErrorMessage } from '@/lib/errors'
import { Users } from 'lucide-react'

function formatMinutes(mins: number | null): string {
  if (mins == null) return '—'
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export default function DirectorAttendancePage() {
  const attendanceEnabled = useModuleEnabled('attendance')
  const { data: records, isLoading, error, refetch } = useDirectorAttendance()

  return (
    <AppShell>
      <PageHeader
        title="Attendance"
        subtitle={attendanceEnabled ? `Today — ${format(new Date(), 'dd MMM yyyy')}` : 'Coming soon'}
      />
      <ContentArea>
        {!attendanceEnabled ? (
          <ModuleDisabledState />
        ) : isLoading ? (
          <SkeletonScreen rows={10} />
        ) : error ? (
          <ErrorState message={apiErrorMessage(error)} onRetry={() => refetch()} />
        ) : !records || records.length === 0 ? (
          <EmptyState
            heading="No attendance data"
            body="No records for today yet."
            icon={Users}
          />
        ) : (
          <div className="rounded-lg border border-surface-border overflow-hidden">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Employee', 'First check-in', 'Last check-out', 'Duration', 'Status'].map(h => (
                    <th
                      key={h}
                      scope="col"
                      className="px-4 py-2 text-left text-xs font-semibold text-text-primary/40 uppercase tracking-wider whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.map(r => (
                  <tr key={r.employee_id} className="border-b border-surface-border last:border-0">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-xs text-text-primary">{r.full_name}</span>
                      <span className="ml-2 text-xs text-text-primary/40 font-mono">
                        {r.employee_code}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-text-primary whitespace-nowrap">
                      {r.first_check_in ? format(new Date(r.first_check_in), 'HH:mm') : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-text-primary whitespace-nowrap">
                      {r.last_check_out ? format(new Date(r.last_check_out), 'HH:mm') : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-text-primary/70">
                      {formatMinutes(r.total_minutes)}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-text-primary/60 uppercase tracking-wider">
                      {r.attendance_state}
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
