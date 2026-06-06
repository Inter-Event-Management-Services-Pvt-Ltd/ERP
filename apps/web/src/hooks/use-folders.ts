import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createFolder, renameFolder, deleteFolder } from '@/lib/api'
import type { CreateFolderPayload, UpdateFolderPayload } from '@/types'

const treeKey = (projectId: string) => ['projects', projectId, 'folders', 'tree']

export function useCreateFolder(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateFolderPayload) => createFolder(projectId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: treeKey(projectId) }),
  })
}

export function useRenameFolder(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ folderId, payload }: { folderId: string; payload: UpdateFolderPayload }) =>
      renameFolder(folderId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: treeKey(projectId) }),
  })
}

export function useDeleteFolder(projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (folderId: string) => deleteFolder(folderId),
    onSuccess: () => qc.invalidateQueries({ queryKey: treeKey(projectId) }),
  })
}
