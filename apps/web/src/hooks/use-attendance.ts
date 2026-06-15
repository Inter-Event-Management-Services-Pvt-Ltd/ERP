import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  checkIn,
  checkOut,
  fetchMyAttendance,
  fetchTeamAttendance,
  correctAttendanceSession,
  fetchDirectorAttendance,
} from '@/lib/api'
import type { CheckInPayload, CheckOutPayload, AttendanceCorrectionPayload } from '@/types'

export const MY_ATTENDANCE_KEY = ['attendance', 'me'] as const
export const TEAM_ATTENDANCE_KEY = ['attendance', 'team'] as const

export function useMyAttendance(params?: { from_date?: string; to_date?: string }) {
  return useQuery({
    queryKey: [...MY_ATTENDANCE_KEY, params],
    queryFn: () => fetchMyAttendance(params),
    staleTime: 30 * 1000,
  })
}

export function useTeamAttendance(params?: {
  employee_id?: string
  from_date?: string
  to_date?: string
}) {
  return useQuery({
    queryKey: [...TEAM_ATTENDANCE_KEY, params],
    queryFn: () => fetchTeamAttendance(params),
    staleTime: 30 * 1000,
  })
}

export function useCheckIn() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CheckInPayload) => checkIn(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: MY_ATTENDANCE_KEY })
      qc.invalidateQueries({ queryKey: TEAM_ATTENDANCE_KEY })
    },
  })
}

export function useCheckOut() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CheckOutPayload) => checkOut(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: MY_ATTENDANCE_KEY })
      qc.invalidateQueries({ queryKey: TEAM_ATTENDANCE_KEY })
    },
  })
}

export function useCorrectAttendanceSession() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      sessionId,
      payload,
    }: {
      sessionId: string
      payload: AttendanceCorrectionPayload
    }) => correctAttendanceSession(sessionId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: MY_ATTENDANCE_KEY })
      qc.invalidateQueries({ queryKey: TEAM_ATTENDANCE_KEY })
    },
  })
}

export function useDirectorAttendance() {
  return useQuery({
    queryKey: ['director', 'attendance'],
    queryFn: fetchDirectorAttendance,
    staleTime: 30 * 1000,
  })
}
