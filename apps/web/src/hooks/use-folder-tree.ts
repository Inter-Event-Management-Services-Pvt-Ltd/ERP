import { useQuery } from '@tanstack/react-query'
import { fetchFolderTree } from '@/lib/api'

export function useFolderTree(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'folders', 'tree'],
    queryFn: () => fetchFolderTree(projectId),
    enabled: Boolean(projectId),
    staleTime: 60 * 1000,
  })
}
