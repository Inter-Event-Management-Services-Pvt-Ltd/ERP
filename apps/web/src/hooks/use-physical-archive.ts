import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listRooms,
  createRoom,
  createLocation,
  getLocationContents,
  createPhysicalFile,
  getPhysicalFile,
  checkoutPhysicalFile,
  returnPhysicalFile,
  movePhysicalFile,
  verifyPhysicalFile,
  getPhysicalFileLabel,
} from '@/lib/api'
import type {
  CreatePhysicalRoomPayload,
  CreatePhysicalLocationPayload,
  CreatePhysicalFilePayload,
  PhysicalFileCheckoutPayload,
  PhysicalFileReturnPayload,
  PhysicalFileMovePayload,
  PhysicalFileVerifyPayload,
} from '@/types'

const ROOMS_KEY = ['archive', 'rooms'] as const

export function useRooms() {
  return useQuery({
    queryKey: ROOMS_KEY,
    queryFn: listRooms,
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateRoom() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreatePhysicalRoomPayload) => createRoom(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ROOMS_KEY }),
  })
}

export function useCreateLocation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreatePhysicalLocationPayload) => createLocation(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ROOMS_KEY }),
  })
}

export function useLocationContents(locationId: string | null) {
  return useQuery({
    queryKey: ['archive', 'locations', locationId, 'contents'],
    queryFn: () => getLocationContents(locationId!),
    enabled: Boolean(locationId),
    staleTime: 30 * 1000,
  })
}

export function useCreatePhysicalFile(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreatePhysicalFilePayload) =>
      createPhysicalFile(projectId, payload),
    onSuccess: (_, payload) => {
      qc.invalidateQueries({
        queryKey: ['archive', 'locations', payload.location_id, 'contents'],
      })
    },
  })
}

export function usePhysicalFile(fileId: string) {
  return useQuery({
    queryKey: ['archive', 'files', fileId],
    queryFn: () => getPhysicalFile(fileId),
    enabled: Boolean(fileId),
    staleTime: 30 * 1000,
  })
}

const fileKey = (fileId: string) => ['archive', 'files', fileId]

export function useCheckoutPhysicalFile(fileId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: PhysicalFileCheckoutPayload) =>
      checkoutPhysicalFile(fileId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: fileKey(fileId) }),
  })
}

export function useReturnPhysicalFile(fileId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: PhysicalFileReturnPayload) =>
      returnPhysicalFile(fileId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: fileKey(fileId) }),
  })
}

export function useMovePhysicalFile(fileId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: PhysicalFileMovePayload) =>
      movePhysicalFile(fileId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: fileKey(fileId) }),
  })
}

export function useVerifyPhysicalFile(fileId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: PhysicalFileVerifyPayload) =>
      verifyPhysicalFile(fileId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: fileKey(fileId) }),
  })
}

export function usePhysicalFileLabel(fileId: string) {
  return useQuery({
    queryKey: ['archive', 'files', fileId, 'label'],
    queryFn: () => getPhysicalFileLabel(fileId),
    enabled: Boolean(fileId),
    staleTime: 5 * 60 * 1000,
  })
}
