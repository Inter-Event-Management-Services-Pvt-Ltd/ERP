import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  createLeaveRequest,
  fetchMyLeaveRequests,
  fetchPendingLeaveRequests,
  approveLeaveRequest,
  rejectLeaveRequest,
  cancelLeaveRequest,
} from '@/lib/api'
import type { CreateLeaveRequestPayload, ReviewLeaveRequestPayload } from '@/types'

export const MY_LEAVE_KEY = ['leave-requests', 'me'] as const
export const PENDING_LEAVE_KEY = ['leave-requests', 'pending'] as const

export function useMyLeaveRequests(params?: { status?: string }) {
  return useQuery({
    queryKey: [...MY_LEAVE_KEY, params],
    queryFn: () => fetchMyLeaveRequests(params),
    staleTime: 30 * 1000,
  })
}

export function usePendingLeaveRequests() {
  return useQuery({
    queryKey: PENDING_LEAVE_KEY,
    queryFn: () => fetchPendingLeaveRequests(),
    staleTime: 30 * 1000,
  })
}

export function useCreateLeaveRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateLeaveRequestPayload) => createLeaveRequest(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: MY_LEAVE_KEY })
    },
  })
}

export function useApproveLeaveRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      requestId,
      payload,
    }: {
      requestId: string
      payload: ReviewLeaveRequestPayload
    }) => approveLeaveRequest(requestId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PENDING_LEAVE_KEY })
      qc.invalidateQueries({ queryKey: MY_LEAVE_KEY })
    },
  })
}

export function useRejectLeaveRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      requestId,
      payload,
    }: {
      requestId: string
      payload: ReviewLeaveRequestPayload
    }) => rejectLeaveRequest(requestId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PENDING_LEAVE_KEY })
      qc.invalidateQueries({ queryKey: MY_LEAVE_KEY })
    },
  })
}

export function useCancelLeaveRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (requestId: string) => cancelLeaveRequest(requestId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: MY_LEAVE_KEY })
      qc.invalidateQueries({ queryKey: PENDING_LEAVE_KEY })
    },
  })
}
