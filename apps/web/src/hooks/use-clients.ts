import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchClients,
  fetchClient,
  createClient,
  updateClient,
  deactivateClient,
} from '@/lib/api'
import type { CreateClientPayload } from '@/types'

export const CLIENTS_KEY = ['clients'] as const

export function useClients() {
  return useQuery({
    queryKey: CLIENTS_KEY,
    queryFn: fetchClients,
    staleTime: 2 * 60 * 1000,
  })
}

export function useClient(id: string) {
  return useQuery({
    queryKey: [...CLIENTS_KEY, id],
    queryFn: () => fetchClient(id),
    enabled: Boolean(id),
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateClient() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateClientPayload) => createClient(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: CLIENTS_KEY }),
  })
}

export function useUpdateClient(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: Partial<CreateClientPayload>) => updateClient(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: CLIENTS_KEY })
      qc.invalidateQueries({ queryKey: [...CLIENTS_KEY, id] })
    },
  })
}

export function useDeactivateClient() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deactivateClient(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: CLIENTS_KEY }),
  })
}
