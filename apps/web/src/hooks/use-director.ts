'use client'

import { useQuery } from '@tanstack/react-query'
import {
  fetchDirectorOverview,
  fetchDirectorProjects,
  fetchDirectorApprovals,
  fetchDirectorOverdueTasks,
  fetchDirectorPhysicalFiles,
  fetchDirectorAuditEvents,
} from '@/lib/api'

export function useDirectorOverview() {
  return useQuery({
    queryKey: ['director', 'overview'],
    queryFn: fetchDirectorOverview,
    staleTime: 60 * 1000,
  })
}

export function useDirectorProjects(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['director', 'projects', params],
    queryFn: () => fetchDirectorProjects(params),
    staleTime: 60 * 1000,
  })
}

export function useDirectorApprovals(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['director', 'approvals', params],
    queryFn: () => fetchDirectorApprovals(params),
    staleTime: 30 * 1000,
  })
}

export function useDirectorOverdueTasks(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['director', 'overdue-tasks', params],
    queryFn: () => fetchDirectorOverdueTasks(params),
    staleTime: 60 * 1000,
  })
}

export function useDirectorPhysicalFiles(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['director', 'physical-files', params],
    queryFn: () => fetchDirectorPhysicalFiles(params),
    staleTime: 60 * 1000,
  })
}

export function useDirectorAuditEvents(params?: {
  action_code?: string
  resource_type?: string
  limit?: number
  offset?: number
}) {
  return useQuery({
    queryKey: ['director', 'audit-events', params],
    queryFn: () => fetchDirectorAuditEvents(params),
    staleTime: 30 * 1000,
  })
}
