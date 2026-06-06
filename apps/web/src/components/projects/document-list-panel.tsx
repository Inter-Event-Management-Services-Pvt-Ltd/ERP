'use client'

import { useState } from 'react'
import {
  FileText,
  Download,
  UploadCloud,
  Loader2,
  Plus,
  RefreshCw,
} from 'lucide-react'
import { useFolderDocuments, useDocumentVersionDownloadUrl, useUploadDocumentVersion } from '@/hooks/use-documents'
import { DocumentUploadDialog } from '@/components/projects/document-upload-dialog'
import { apiErrorMessage } from '@/lib/errors'
import { cn } from '@/lib/utils'
import type { Document } from '@/types'

interface DocumentListPanelProps {
  folderId: string
  folderName: string
  projectId: string
  canUpload: boolean
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function mimeLabel(mime: string): string {
  if (mime.startsWith('image/')) return 'Image'
  if (mime === 'application/pdf') return 'PDF'
  if (mime.includes('word') || mime.includes('document')) return 'Word'
  if (mime.includes('sheet') || mime.includes('excel') || mime.includes('csv')) return 'Spreadsheet'
  if (mime.includes('presentation') || mime.includes('powerpoint')) return 'Presentation'
  if (mime.startsWith('text/')) return 'Text'
  return 'File'
}

export function DocumentListPanel({
  folderId,
  folderName,
  projectId,
  canUpload,
}: DocumentListPanelProps) {
  const { data: documents = [], isLoading, error, refetch } = useFolderDocuments(folderId, projectId)
  const [showUpload, setShowUpload] = useState(false)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-sans font-semibold text-text-primary">
          <span className="font-mono text-accent-saffron">{folderName}</span>
          {!isLoading && (
            <span className="ml-2 text-text-primary/40 font-sans font-normal">
              ({documents.length} document{documents.length !== 1 ? 's' : ''})
            </span>
          )}
        </h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => refetch()}
            aria-label="Refresh documents"
            className="text-text-primary/30 hover:text-text-primary/60 transition-colors p-1 rounded"
          >
            <RefreshCw size={13} aria-hidden="true" />
          </button>
          {canUpload && (
            <button
              type="button"
              onClick={() => setShowUpload(true)}
              className="flex items-center gap-1.5 text-xs font-sans font-medium px-3 py-1.5 rounded-md bg-accent-saffron/90 text-surface-deep hover:bg-accent-saffron transition-colors"
            >
              <Plus size={12} aria-hidden="true" />
              Upload
            </button>
          )}
        </div>
      </div>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-14 rounded-lg bg-surface-border/40 shimmer" />
          ))}
        </div>
      )}

      {!isLoading && error && (
        <p className="text-sm font-sans text-accent-critical py-2">
          {apiErrorMessage(error)}
        </p>
      )}

      {!isLoading && !error && documents.length === 0 && (
        <div className="py-8 text-center">
          <FileText size={24} className="text-text-primary/20 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm font-sans text-text-primary/40">No documents in this folder.</p>
          {canUpload && (
            <button
              type="button"
              onClick={() => setShowUpload(true)}
              className="mt-3 text-xs font-sans text-accent-saffron/70 hover:text-accent-saffron transition-colors"
            >
              Upload the first document
            </button>
          )}
        </div>
      )}

      {!isLoading && !error && documents.length > 0 && (
        <ul className="space-y-2">
          {documents.map((doc) => (
            <DocumentRow
              key={doc.id}
              doc={doc}
              folderId={folderId}
              canUpload={canUpload}
            />
          ))}
        </ul>
      )}

      <DocumentUploadDialog
        open={showUpload}
        folderId={folderId}
        folderName={folderName}
        onClose={() => setShowUpload(false)}
      />
    </div>
  )
}

function DocumentRow({
  doc,
  folderId,
  canUpload,
}: {
  doc: Document
  folderId: string
  canUpload: boolean
}) {
  const [versionFile, setVersionFile] = useState<File | null>(null)
  const [versionError, setVersionError] = useState<string | null>(null)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  const { mutate: getDownloadUrl, isPending: downloading } = useDocumentVersionDownloadUrl()
  const { mutate: uploadVersion, isPending: uploadingVersion } = useUploadDocumentVersion(
    doc.id,
    folderId
  )

  function handleDownload() {
    if (!doc.latest_version) return
    setDownloadError(null)
    getDownloadUrl(doc.latest_version.id, {
      onSuccess: (res) => window.open(res.url, '_blank', 'noopener,noreferrer'),
      onError: (err) => setDownloadError(apiErrorMessage(err)),
    })
  }

  function handleVersionSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null
    if (!f) return
    setVersionFile(f)
    setVersionError(null)
    const fd = new FormData()
    fd.append('file', f)
    uploadVersion(fd, {
      onSuccess: () => setVersionFile(null),
      onError: (err) => {
        setVersionError(apiErrorMessage(err))
        setVersionFile(null)
      },
    })
    e.target.value = ''
  }

  const v = doc.latest_version

  return (
    <li className="rounded-lg border border-surface-border bg-surface-base px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <FileText
            size={16}
            className="flex-none text-accent-saffron/70 mt-0.5"
            aria-hidden="true"
          />
          <div className="min-w-0">
            <p className="text-sm font-sans text-text-primary truncate">{doc.display_name}</p>
            {v && (
              <p className="text-xs font-mono text-text-primary/40 mt-0.5">
                v{v.version_number} · {mimeLabel(v.mime_type)} · {formatBytes(v.size_bytes)}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-none">
          {canUpload && (
            <label
              title="Upload new version"
              aria-label={`Upload new version of ${doc.display_name}`}
              className={cn(
                'cursor-pointer p-1 rounded transition-colors',
                uploadingVersion
                  ? 'text-text-primary/20 pointer-events-none'
                  : 'text-text-primary/30 hover:text-accent-saffron'
              )}
            >
              {uploadingVersion ? (
                <Loader2 size={13} className="animate-spin" aria-hidden="true" />
              ) : (
                <UploadCloud size={13} aria-hidden="true" />
              )}
              <input
                type="file"
                className="sr-only"
                onChange={handleVersionSelect}
                disabled={uploadingVersion}
              />
            </label>
          )}

          <button
            type="button"
            onClick={handleDownload}
            disabled={!v || downloading}
            aria-label={`Download ${doc.display_name}`}
            className="p-1 rounded transition-colors text-text-primary/30 hover:text-accent-saffron disabled:opacity-30 disabled:cursor-not-allowed"
          >
            {downloading ? (
              <Loader2 size={13} className="animate-spin" aria-hidden="true" />
            ) : (
              <Download size={13} aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {(versionError || downloadError) && (
        <p role="alert" className="text-xs font-sans text-accent-critical mt-1.5">
          {versionError ?? downloadError}
        </p>
      )}
    </li>
  )
}
