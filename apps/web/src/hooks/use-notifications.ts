'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchNotifications, markNotificationRead } from '@/lib/api'

export const NOTIFICATIONS_QUERY_KEY = ['notifications'] as const

export function useNotifications(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: [...NOTIFICATIONS_QUERY_KEY, params],
    queryFn: () => fetchNotifications(params),
    staleTime: 60 * 1000,
    retry: false,
  })
}

export function useUnreadCount() {
  const { data } = useNotifications({ limit: 100 })
  return (data ?? []).filter((n) => !n.read_at).length
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_QUERY_KEY })
    },
  })
}
