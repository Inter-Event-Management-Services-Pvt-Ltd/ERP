import { useQuery } from '@tanstack/react-query'
import {
  fetchProjectTypes,
  fetchProjectStatuses,
  fetchPriorityLevels,
  fetchConfidentialityLevels,
  fetchDocumentTypes,
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
