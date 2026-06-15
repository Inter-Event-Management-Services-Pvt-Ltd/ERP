'use client'

import { useMemo, useState } from 'react'
import { format } from 'date-fns'
import { LogIn, LogOut, Loader2, Pencil } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { SearchInput } from '@/components/ui/search-input'
import { CorrectionDialog } from '@/components/attendance/correction-dialog'
import { useMe } from '@/hooks/use-me'
import { useEmployeeSearch } from '@/hooks/use-employees'
import {
  useMyAttendance,
  useTeamAttendance,
  useCheckIn,
  useCheckOut,
} from '@/hooks/use-attendance'
import { apiErrorMessage } from '@/lib/errors'
import type { AttendanceSession } from '@/types'

function formatDuration(minutes: number | null): string {
  if (minutes == null) return '—'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${h}h ${m}m`
}

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  return format(new Date(iso), 'dd MMM yyyy, HH:mm')
}

function SessionRow({
  session,
  showEmployee,
  canCorrect,
  onCorrect,
}: {
  session: AttendanceSession
  showEmployee: boolean
  canCorrect: boolean
  onCorrect: (session: AttendanceSession) => void
}) {
  return (
    <tr className="border-b border-surface-border last:border-0">
      {showEmployee && (
        <td className="px-4 py-3 text-text-primary/80 whitespace-nowrap">
          {session.employee ? (
            <span>
              {session.employee.full_name}{' '}
              <span className="text-text-primary/40 font-mono text-xs">
                {session.employee.employee_code}
              </span>
            </span>
          ) : (
            '—'
          )}
        </td>
      )}
      <td className="px-4 py-3 font-mono text-xs text-text-primary/70 whitespace-nowrap">
        {formatTime(session.checked_in_at)}
      </td>
      <td className="px-4 py-3 font-mono text-xs text-text-primary/70 whitespace-nowrap">
        {session.checked_out_at ? formatTime(session.checked_out_at) : (
          <Badge variant="active">Open</Badge>
        )}
      </td>
      <td className="px-4 py-3 font-mono text-xs text-text-primary/70 whitespace-nowrap">
        {formatDuration(session.total_minutes)}
      </td>
      <td className="px-4 py-3 text-xs text-text-primary/50 whitespace-nowrap">
        {session.source}
      </td>
      <td className="px-4 py-3 text-sm text-text-primary/60 max-w-xs truncate">
        {session.remarks ?? '—'}
        {session.correction_reason && (
          <span className="ml-1.5 text-accent-warning text-xs">(corrected)</span>
        )}
      </td>
      {canCorrect && (
        <td className="px-4 py-3 text-right whitespace-nowrap">
          <button
            type="button"
            onClick={() => onCorrect(session)}
            className="inline-flex items-center gap-1 text-xs font-sans text-accent-saffron/70 hover:text-accent-saffron transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron rounded"
            aria-label={`Correct session starting ${formatTime(session.checked_in_at)}`}
          >
            <Pencil size={12} aria-hidden="true" />
            Correct
          </button>
        </td>
      )}
    </tr>
  )
}

export default function AttendancePage() {
  const { data: user } = useMe()
  const canViewAll = (user?.isSuperUser || user?.permissions.includes('attendance.view_all')) ?? false
  const canCorrect = (user?.isSuperUser || user?.permissions.includes('attendance.correct')) ?? false

  const { data: mySessions, isLoading, error, refetch } = useMyAttendance()
  const { mutate: checkIn, isPending: checkingIn } = useCheckIn()
  const { mutate: checkOut, isPending: checkingOut } = useCheckOut()

  const [actionError, setActionError] = useState<string | null>(null)
  const [remarks, setRemarks] = useState('')
  const [correctingSession, setCorrectingSession] = useState<AttendanceSession | null>(null)

  const [teamSearch, setTeamSearch] = useState('')
  const { data: employeeMatches = [] } = useEmployeeSearch(teamSearch)
  const [teamEmployeeId, setTeamEmployeeId] = useState<string | undefined>(undefined)
  const {
    data: teamSessions,
    isLoading: teamLoading,
    error: teamError,
    refetch: refetchTeam,
  } = useTeamAttendance(canViewAll ? { employee_id: teamEmployeeId } : undefined)

  const openSession = useMemo(
    () => (mySessions ?? []).find((s) => !s.checked_out_at) ?? null,
    [mySessions]
  )

  function handleCheckIn() {
    setActionError(null)
    checkIn(
      { remarks: remarks.trim() ? remarks.trim() : undefined },
      {
        onSuccess: () => setRemarks(''),
        onError: (err) => setActionError(apiErrorMessage(err)),
      }
    )
  }

  function handleCheckOut() {
    setActionError(null)
    checkOut(
      { remarks: remarks.trim() ? remarks.trim() : undefined },
      {
        onSuccess: () => setRemarks(''),
        onError: (err) => setActionError(apiErrorMessage(err)),
      }
    )
  }

  return (
    <AppShell>
      <PageHeader title="Attendance" subtitle="My records" />

      <ContentArea>
        {/* Check-in / Check-out card */}
        <div className="rounded-lg border border-surface-border bg-surface-raised px-5 py-4 mb-6 max-w-xl">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <p className="text-xs uppercase tracking-wider text-text-primary/40 font-sans mb-1">
                Current status
              </p>
              {openSession ? (
                <p className="text-sm font-sans text-text-primary">
                  Checked in at{' '}
                  <span className="font-mono text-accent-saffron">
                    {formatTime(openSession.checked_in_at)}
                  </span>
                </p>
              ) : (
                <p className="text-sm font-sans text-text-primary/60">Not checked in</p>
              )}
            </div>
            <button
              type="button"
              onClick={openSession ? handleCheckOut : handleCheckIn}
              disabled={checkingIn || checkingOut}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-sans font-medium rounded-md bg-accent-saffron text-surface-deep hover:bg-accent-warning disabled:opacity-40 transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron focus-visible:ring-offset-2 focus-visible:ring-offset-surface-raised"
            >
              {(checkingIn || checkingOut) && (
                <Loader2 size={14} className="animate-spin" aria-hidden="true" />
              )}
              {openSession ? (
                <>
                  <LogOut size={14} aria-hidden="true" /> Check Out
                </>
              ) : (
                <>
                  <LogIn size={14} aria-hidden="true" /> Check In
                </>
              )}
            </button>
          </div>

          <div className="mt-3">
            <label htmlFor="attendance-remarks" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
              Remarks (optional)
            </label>
            <input
              id="attendance-remarks"
              type="text"
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="e.g. working from site"
              className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary placeholder:text-text-primary/30 focus:outline-none focus:ring-2 focus:ring-accent-saffron"
            />
          </div>

          {actionError && (
            <p role="alert" className="mt-2 text-xs font-sans text-accent-critical">
              {actionError}
            </p>
          )}
        </div>

        {/* My history */}
        <h2 className="font-serif italic text-lg text-text-primary mb-3">My History</h2>

        {isLoading && <SkeletonScreen rows={4} />}

        {!isLoading && error && (
          <ErrorState
            message={error instanceof Error ? error.message : 'Failed to load attendance'}
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && (mySessions ?? []).length === 0 && (
          <EmptyState heading="No attendance records" body="Check in to start recording your attendance." />
        )}

        {!isLoading && !error && (mySessions ?? []).length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border mb-8">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Checked In', 'Checked Out', 'Duration', 'Source', 'Remarks'].map((h) => (
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
                {(mySessions ?? []).map((s) => (
                  <SessionRow
                    key={s.id}
                    session={s}
                    showEmployee={false}
                    canCorrect={false}
                    onCorrect={() => {}}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Team attendance */}
        {canViewAll && (
          <>
            <h2 className="font-serif italic text-lg text-text-primary mb-3">Team Attendance</h2>

            <div className="flex flex-wrap gap-3 mb-4">
              <SearchInput
                value={teamSearch}
                onChange={(v) => {
                  setTeamSearch(v)
                  if (!v) setTeamEmployeeId(undefined)
                }}
                placeholder="Search employee…"
                className="w-64"
              />
              {employeeMatches.length > 0 && teamSearch && (
                <select
                  value={teamEmployeeId ?? ''}
                  onChange={(e) => setTeamEmployeeId(e.target.value || undefined)}
                  aria-label="Select employee"
                  className="rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
                >
                  <option value="">All matching employees</option>
                  {employeeMatches.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.full_name} ({emp.employee_code})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {teamLoading && <SkeletonScreen rows={4} />}

            {!teamLoading && teamError && (
              <ErrorState
                message={teamError instanceof Error ? teamError.message : 'Failed to load team attendance'}
                onRetry={() => refetchTeam()}
              />
            )}

            {!teamLoading && !teamError && (teamSessions ?? []).length === 0 && (
              <EmptyState heading="No team records" body="No attendance sessions found for this filter." />
            )}

            {!teamLoading && !teamError && (teamSessions ?? []).length > 0 && (
              <div className="overflow-x-auto rounded-lg border border-surface-border">
                <table className="w-full text-sm font-sans">
                  <thead>
                    <tr className="border-b border-surface-border bg-surface-raised">
                      {['Employee', 'Checked In', 'Checked Out', 'Duration', 'Source', 'Remarks'].map((h) => (
                        <th
                          key={h}
                          scope="col"
                          className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap"
                        >
                          {h}
                        </th>
                      ))}
                      {canCorrect && <th scope="col" className="px-4 py-2.5" />}
                    </tr>
                  </thead>
                  <tbody>
                    {(teamSessions ?? []).map((s) => (
                      <SessionRow
                        key={s.id}
                        session={s}
                        showEmployee
                        canCorrect={canCorrect}
                        onCorrect={setCorrectingSession}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </ContentArea>

      <CorrectionDialog session={correctingSession} onClose={() => setCorrectingSession(null)} />
    </AppShell>
  )
}
