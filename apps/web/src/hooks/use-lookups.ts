import { useQuery } from '@tanstack/react-query'
import {
  fetchProjectTypes,
  fetchProjectStatuses,
  fetchPriorityLevels,
  fetchConfidentialityLevels,
  fetchDocumentTypes,
  fetchLeaveTypes,
  fetchTaskStatuses,
} from '@/lib/api'

export function useProjectTypes() {
  return useQuery({
    queryKey: ['project-types'],
    queryFn: fetchProjectTypes,
    staleTime: 10 * 60 * 1000,
  })
}

export function useProjectStatuses() {
  return useQuery({
    queryKey: ['project-statuses'],
    queryFn: fetchProjectStatuses,
    staleTime: 10 * 60 * 1000,
  })
}

export function usePriorityLevels() {
  return useQuery({
    queryKey: ['priority-levels'],
    queryFn: fetchPriorityLevels,
    staleTime: 10 * 60 * 1000,
  })
}

export function useConfidentialityLevels() {
  return useQuery({
    queryKey: ['confidentiality-levels'],
    queryFn: fetchConfidentialityLevels,
    staleTime: 10 * 60 * 1000,
  })
}

export function useDocumentTypes() {
  return useQuery({
    queryKey: ['document-types'],
    queryFn: fetchDocumentTypes,
    staleTime: 10 * 60 * 1000,
  })
}

export function useLeaveTypes() {
  return useQuery({
    queryKey: ['leave-types'],
    queryFn: fetchLeaveTypes,
    staleTime: 10 * 60 * 1000,
  })
}

export function useTaskStatuses() {
  return useQuery({
    queryKey: ['task-statuses'],
    queryFn: fetchTaskStatuses,
    staleTime: 10 * 60 * 1000,
  })
}
