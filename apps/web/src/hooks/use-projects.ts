import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import {
  fetchProjects,
  fetchProject,
  fetchProjectMembers,
  createProject,
  updateProject,
  addProjectMember,
  removeProjectMember,
  updateProjectMemberRole,
} from '@/lib/api'
import type {
  CreateProjectPayload,
  UpdateProjectPayload,
  AddProjectMemberPayload,
  ProjectMemberRole,
} from '@/types'

export const PROJECTS_KEY = ['projects'] as const

export function useProjects(includeArchived = false) {
  return useQuery({
    queryKey: includeArchived ? [...PROJECTS_KEY, 'with-archived'] : PROJECTS_KEY,
    queryFn: () => fetchProjects({ includeArchived }),
    staleTime: 2 * 60 * 1000,
    placeholderData: keepPreviousData,
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

export function useProjectMembers(projectId: string) {
  return useQuery({
    queryKey: [...PROJECTS_KEY, projectId, 'members'],
    queryFn: () => fetchProjectMembers(projectId),
    enabled: Boolean(projectId),
    staleTime: 2 * 60 * 1000,
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

export function useUpdateProjectMemberRole(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      employeeId,
      accessLevel,
    }: {
      employeeId: string
      accessLevel: ProjectMemberRole
    }) =>
      updateProjectMemberRole(projectId, employeeId, { access_level: accessLevel }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: [...PROJECTS_KEY, projectId] }),
  })
}
