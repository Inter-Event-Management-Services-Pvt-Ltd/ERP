import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchProjects,
  fetchProject,
  createProject,
  updateProject,
  addProjectMember,
  removeProjectMember,
} from '@/lib/api'
import type {
  CreateProjectPayload,
  UpdateProjectPayload,
  AddProjectMemberPayload,
} from '@/types'

export const PROJECTS_KEY = ['projects'] as const

export function useProjects() {
  return useQuery({
    queryKey: PROJECTS_KEY,
    queryFn: fetchProjects,
    staleTime: 2 * 60 * 1000,
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: [...PROJECTS_KEY, id],
    queryFn: () => fetchProject(id),
    enabled: Boolean(id),
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateProject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateProjectPayload) => createProject(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: PROJECTS_KEY }),
  })
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateProjectPayload) => updateProject(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PROJECTS_KEY })
      qc.invalidateQueries({ queryKey: [...PROJECTS_KEY, id] })
    },
  })
}

export function useAddProjectMember(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AddProjectMemberPayload) =>
      addProjectMember(projectId, payload),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [...PROJECTS_KEY, projectId] }),
  })
}

export function useRemoveProjectMember(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (employeeId: string) =>
      removeProjectMember(projectId, employeeId),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [...PROJECTS_KEY, projectId] }),
  })
}
