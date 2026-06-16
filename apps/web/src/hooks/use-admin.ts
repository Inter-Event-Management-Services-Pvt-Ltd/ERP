'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchPolicies,
  createPolicy,
  updatePolicy,
  fetchFolderTemplates,
  createFolderTemplate,
  fetchFolderTemplate,
  updateFolderTemplate,
  createFolderTemplateItem,
  updateFolderTemplateItem,
  updatePhysicalRoom,
  updatePhysicalLocation,
  fetchAuditEvents,
} from '@/lib/api'
import type {
  CreatePolicyPayload,
  UpdatePolicyPayload,
  CreateFolderTemplatePayload,
  CreateFolderTemplateItemPayload,
  UpdateFolderTemplateItemPayload,
  UpdatePhysicalRoomPayload,
  UpdatePhysicalLocationPayload,
} from '@/types'

// ─── Policies ─────────────────────────────────────────────────────────────────

export function usePolicies() {
  return useQuery({
    queryKey: ['policies'],
    queryFn: fetchPolicies,
    staleTime: 60 * 1000,
  })
}

export function useCreatePolicy() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ payload, overrideReason }: { payload: CreatePolicyPayload; overrideReason?: string }) =>
      createPolicy(payload, overrideReason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['policies'] })
    },
  })
}

export function useUpdatePolicy() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      payload,
      overrideReason,
    }: {
      id: string
      payload: UpdatePolicyPayload
      overrideReason?: string
    }) => updatePolicy(id, payload, overrideReason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['policies'] })
    },
  })
}

// ─── Folder templates ─────────────────────────────────────────────────────────

export function useFolderTemplates() {
  return useQuery({
    queryKey: ['folder-templates'],
    queryFn: fetchFolderTemplates,
    staleTime: 5 * 60 * 1000,
  })
}

export function useFolderTemplate(templateId: string) {
  return useQuery({
    queryKey: ['folder-templates', templateId],
    queryFn: () => fetchFolderTemplate(templateId),
    staleTime: 30 * 1000,
    enabled: !!templateId,
  })
}

export function useCreateFolderTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateFolderTemplatePayload) => createFolderTemplate(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['folder-templates'] })
    },
  })
}

export function useUpdateFolderTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<CreateFolderTemplatePayload> }) =>
      updateFolderTemplate(id, payload),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: ['folder-templates', id] })
      qc.invalidateQueries({ queryKey: ['folder-templates'] })
    },
  })
}

export function useCreateFolderTemplateItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      templateId,
      payload,
    }: {
      templateId: string
      payload: CreateFolderTemplateItemPayload
    }) => createFolderTemplateItem(templateId, payload),
    onSuccess: (_data, { templateId }) => {
      qc.invalidateQueries({ queryKey: ['folder-templates', templateId] })
    },
  })
}

export function useUpdateFolderTemplateItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      templateId,
      itemId,
      payload,
    }: {
      templateId: string
      itemId: string
      payload: UpdateFolderTemplateItemPayload
    }) => updateFolderTemplateItem(itemId, payload),
    onSuccess: (_data, { templateId }) => {
      qc.invalidateQueries({ queryKey: ['folder-templates', templateId] })
    },
  })
}

// ─── Physical archive admin writes ────────────────────────────────────────────

export function useUpdatePhysicalRoom() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdatePhysicalRoomPayload }) =>
      updatePhysicalRoom(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['rooms'] })
    },
  })
}

export function useUpdatePhysicalLocation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdatePhysicalLocationPayload }) =>
      updatePhysicalLocation(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['locations'] })
    },
  })
}

// ─── Full audit explorer ──────────────────────────────────────────────────────

export function useAuditEvents(params?: {
  action_code?: string
  resource_type?: string
  resource_id?: string
  actor_employee_id?: string
  created_from?: string
  created_to?: string
  limit?: number
  offset?: number
}) {
  return useQuery({
    queryKey: ['audit-events', params],
    queryFn: () => fetchAuditEvents(params),
    staleTime: 30 * 1000,
  })
}
