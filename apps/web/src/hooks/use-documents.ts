import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  searchDocuments,
  getDocument,
  uploadDocument,
  uploadDocumentVersion,
  getDocumentVersionDownloadUrl,
} from '@/lib/api'

export function useFolderDocuments(folderId: string | null, projectId: string) {
  return useQuery({
    queryKey: ['documents', 'folder', folderId],
    queryFn: () => searchDocuments({ folder_id: folderId!, project_id: projectId }),
    enabled: Boolean(folderId),
    staleTime: 30 * 1000,
  })
}

export function useDocument(documentId: string | null) {
  return useQuery({
    queryKey: ['documents', documentId],
    queryFn: () => getDocument(documentId!),
    enabled: Boolean(documentId),
    staleTime: 60 * 1000,
  })
}

export function useUploadDocument(folderId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (formData: FormData) => uploadDocument(folderId, formData),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ['documents', 'folder', folderId] }),
  })
}

export function useUploadDocumentVersion(documentId: string, folderId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (formData: FormData) => uploadDocumentVersion(documentId, formData),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents', documentId] })
      qc.invalidateQueries({ queryKey: ['documents', 'folder', folderId] })
    },
  })
}

export function useDocumentVersionDownloadUrl() {
  return useMutation({
    mutationFn: (versionId: string) => getDocumentVersionDownloadUrl(versionId),
  })
}
