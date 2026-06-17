'use client'

import { useQuery, keepPreviousData } from '@tanstack/react-query'
import {
  fetchDirectorOverview,
  fetchDirectorProjects,
  fetchDirectorApprovals,
  fetchDirectorOverdueTasks,
  fetchDirectorPhysicalFiles,
  fetchDirectorAuditEvents,
  fetchDirectorUpcomingEvents,
  fetchDirectorMissingDocuments,
  fetchDirectorVerificationReminders,
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
    placeholderData: keepPreviousData,
  })
}

export function useDirectorUpcomingEvents(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['director', 'upcoming-events', params],
    queryFn: () => fetchDirectorUpcomingEvents(params),
    staleTime: 60 * 1000,
  })
}

export function useDirectorMissingDocuments(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['director', 'missing-documents', params],
    queryFn: () => fetchDirectorMissingDocuments(params),
    staleTime: 5 * 60 * 1000,
  })
}

export function useDirectorVerificationReminders(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['director', 'verification-reminders', params],
    queryFn: () => fetchDirectorVerificationReminders(params),
    staleTime: 5 * 60 * 1000,
  })
}
