import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createExport, listExports, getExportDownloadUrl } from '@/lib/api'
import type { ExportStatus } from '@/types'

const ACTIVE_STATUSES: ExportStatus[] = ['QUEUED', 'PROCESSING']

export function useProjectExports(projectId: string) {
  const { data: exports = [], ...rest } = useQuery({
    queryKey: ['exports', projectId],
    queryFn: () => listExports(projectId),
    staleTime: 10 * 1000,
    refetchInterval: (query) => {
      const data = query.state.data ?? []
      const hasActive = data.some((e) => ACTIVE_STATUSES.includes(e.status))
      return hasActive ? 5000 : false
    },
  })
  return { data: exports, ...rest }
}

export function useCreateExport(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => createExport(projectId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['exports', projectId] }),
  })
}

export function useExportDownloadUrl() {
  return useMutation({
    mutationFn: (exportId: string) => getExportDownloadUrl(exportId),
  })
}
