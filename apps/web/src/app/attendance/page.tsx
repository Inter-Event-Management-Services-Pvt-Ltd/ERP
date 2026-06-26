'use client'

import { format } from 'date-fns'
import { LogIn, LogOut, Clock } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { ModuleDisabledState } from '@/components/states/module-disabled-state'
import { useMyAttendance, useCheckIn, useCheckOut } from '@/hooks/use-attendance'
import { useModuleEnabled } from '@/hooks/use-modules'
import { apiErrorMessage } from '@/lib/errors'

function formatDuration(mins: number | null): string {
  if (mins == null) return '—'
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export default function AttendancePage() {
  const attendanceEnabled = useModuleEnabled('attendance')
  const { data: sessions, isLoading, error, refetch } = useMyAttendance()
  const { mutate: doCheckIn, isPending: checkingIn, error: checkInError } = useCheckIn()
  const { mutate: doCheckOut, isPending: checkingOut, error: checkOutError } = useCheckOut()

  const openSession = sessions?.find(s => s.checked_out_at == null)
  const actionError = checkInError || checkOutError

  return (
    <AppShell>
      <PageHeader
        title="Attendance"
        subtitle={attendanceEnabled ? 'My records' : 'Not active for this rollout'}
      />
      <ContentArea>
        {!attendanceEnabled ? (
          <ModuleDisabledState />
        ) : isLoading ? (
          <SkeletonScreen rows={8} />
        ) : error ? (
          <ErrorState message={apiErrorMessage(error)} onRetry={() => refetch()} />
        ) : (
          <div className="space-y-4">
            {/* Status + action */}
            <div className="rounded-lg border border-surface-border bg-surface-raised p-4 flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-mono uppercase tracking-wider text-text-primary/55">
                  {openSession ? 'Currently checked in' : 'Not checked in'}
                </p>
                {openSession && (
                  <p className="text-sm font-mono text-text-primary/70 mt-0.5">
                    Since {format(new Date(openSession.checked_in_at), 'HH:mm')}
                  </p>
                )}
                {actionError && (
                  <p className="text-xs text-accent-critical mt-1">{apiErrorMessage(actionError)}</p>
                )}
              </div>
              {openSession ? (
                <button
                  onClick={() => doCheckOut({})}
                  disabled={checkingOut}
                  aria-label="Check out"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-deep border border-surface-border text-text-primary text-sm font-sans hover:border-accent-saffron/40 transition-colors disabled:opacity-50"
                >
                  <LogOut size={14} aria-hidden="true" />
                  Check out
                </button>
              ) : (
                <button
                  onClick={() => doCheckIn({})}
                  disabled={checkingIn}
                  aria-label="Check in"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent-saffron text-surface-deep text-sm font-sans hover:bg-accent-saffron/80 transition-colors disabled:opacity-50"
                >
                  <LogIn size={14} aria-hidden="true" />
                  Check in
                </button>
              )}
            </div>

            {/* History */}
            {!sessions || sessions.length === 0 ? (
              <EmptyState
                heading="No records"
                body="Your attendance history will appear here."
                icon={Clock}
              />
            ) : (
              <div className="rounded-lg border border-surface-border overflow-hidden">
                <table className="w-full text-sm font-sans">
                  <thead>
                    <tr className="border-b border-surface-border bg-surface-raised">
                      {['Date', 'Check in', 'Check out', 'Duration'].map(h => (
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
                    {sessions.map(s => (
                      <tr key={s.id} className="border-b border-surface-border last:border-0">
                        <td className="px-4 py-3 text-xs text-text-primary/70 font-mono whitespace-nowrap">
                          {format(new Date(s.checked_in_at), 'dd MMM yyyy')}
                        </td>
                        <td className="px-4 py-3 text-xs font-mono text-text-primary whitespace-nowrap">
                          {format(new Date(s.checked_in_at), 'HH:mm')}
                        </td>
                        <td className="px-4 py-3 text-xs font-mono text-text-primary whitespace-nowrap">
                          {s.checked_out_at
                            ? format(new Date(s.checked_out_at), 'HH:mm')
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-xs font-mono text-text-primary/70">
                          {formatDuration(s.total_minutes)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
