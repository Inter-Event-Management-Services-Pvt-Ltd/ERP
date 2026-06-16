'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchApprovalTypes,
  fetchApprovals,
  createApproval,
  fetchApproval,
  approveApproval,
  rejectApproval,
  requestApprovalRevision,
} from '@/lib/api'
import type { CreateApprovalPayload, ReviewApprovalPayload } from '@/types'

export function useApprovalTypes() {
  return useQuery({
    queryKey: ['approval-types'],
    queryFn: fetchApprovalTypes,
    staleTime: 10 * 60 * 1000,
  })
}

export function useApprovals(params?: { status?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['approvals', params],
    queryFn: () => fetchApprovals(params),
    staleTime: 30 * 1000,
  })
}

export function useApproval(id: string) {
  return useQuery({
    queryKey: ['approvals', id],
    queryFn: () => fetchApproval(id),
    staleTime: 30 * 1000,
    enabled: !!id,
  })
}

export function useCreateApproval() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateApprovalPayload) => createApproval(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['approvals'] })
    },
  })
}

export function useApproveApproval() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ReviewApprovalPayload }) =>
      approveApproval(id, payload),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: ['approvals', id] })
      qc.invalidateQueries({ queryKey: ['approvals'] })
    },
  })
}

export function useRejectApproval() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ReviewApprovalPayload }) =>
      rejectApproval(id, payload),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: ['approvals', id] })
      qc.invalidateQueries({ queryKey: ['approvals'] })
    },
  })
}

export function useRequestRevision() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ReviewApprovalPayload }) =>
      requestApprovalRevision(id, payload),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: ['approvals', id] })
      qc.invalidateQueries({ queryKey: ['approvals'] })
    },
  })
}
