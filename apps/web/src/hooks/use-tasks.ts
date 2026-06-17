import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query'
import {
  fetchTasks,
  getTask,
  createTask,
  updateTask,
  addTaskAssignees,
  addTaskComment,
  linkTaskDocument,
} from '@/lib/api'
import type {
  CreateTaskPayload,
  UpdateTaskPayload,
  AddTaskAssigneesPayload,
  AddTaskCommentPayload,
  LinkTaskDocumentPayload,
} from '@/types'

export const TASKS_KEY = ['tasks'] as const

export function useTasks(params?: {
  project_id?: string
  assigned_to_me?: boolean
  status_code?: string
}) {
  return useQuery({
    queryKey: [...TASKS_KEY, params],
    queryFn: () => fetchTasks(params),
    staleTime: 30 * 1000,
    placeholderData: keepPreviousData,
  })
}

export function useTask(taskId: string) {
  return useQuery({
    queryKey: [...TASKS_KEY, taskId],
    queryFn: () => getTask(taskId),
    enabled: !!taskId,
    staleTime: 30 * 1000,
  })
}

export function useCreateTask() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateTaskPayload) => createTask(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: TASKS_KEY })
    },
  })
}

export function useUpdateTask(taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateTaskPayload) => updateTask(taskId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: TASKS_KEY })
      qc.invalidateQueries({ queryKey: [...TASKS_KEY, taskId] })
    },
  })
}

export function useAddTaskAssignees(taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AddTaskAssigneesPayload) => addTaskAssignees(taskId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: TASKS_KEY })
      qc.invalidateQueries({ queryKey: [...TASKS_KEY, taskId] })
    },
  })
}

export function useAddTaskComment(taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AddTaskCommentPayload) => addTaskComment(taskId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [...TASKS_KEY, taskId] })
    },
  })
}

export function useLinkTaskDocument(taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: LinkTaskDocumentPayload) => linkTaskDocument(taskId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: TASKS_KEY })
      qc.invalidateQueries({ queryKey: [...TASKS_KEY, taskId] })
    },
  })
}
