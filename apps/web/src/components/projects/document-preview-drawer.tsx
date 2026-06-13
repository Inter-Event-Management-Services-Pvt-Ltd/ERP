'use client'

import { useEffect, useState } from 'react'
import { X, Download, Loader2, FileWarning, FileX } from 'lucide-react'
import { useDocumentVersionDownloadUrl } from '@/hooks/use-documents'
import { apiErrorMessage } from '@/lib/errors'
import type { Document } from '@/types'

interface DocumentPreviewDrawerProps {
  document: Document | null
  onClose: () => void
}

type PreviewKind = 'image' | 'pdf' | 'text'

function previewKindFor(mimeType: string): PreviewKind | null {
  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType === 'application/pdf') return 'pdf'
  if (mimeType.startsWith('text/')) return 'text'
  return null
}

export function DocumentPreviewDrawer({ document, onClose }: DocumentPreviewDrawerProps) {
  const open = Boolean(document)
  const version = document?.latest_version ?? null
  const previewKind = version ? previewKindFor(version.mime_type) : null
  const previewable = Boolean(version?.preview_supported) && previewKind !== null

  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  const { mutate: getPreviewUrl, isPending: previewLoading } = useDocumentVersionDownloadUrl()
  const { mutate: getDownloadUrl, isPending: downloading } = useDocumentVersionDownloadUrl()

  useEffect(() => {
    setPreviewUrl(null)
    setPreviewError(null)
    setDownloadError(null)

    if (!open || !version || !previewable) return

    getPreviewUrl(version.id, {
      onSuccess: (res) => setPreviewUrl(res.url),
      onError: (err) => setPreviewError(apiErrorMessage(err)),
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, version?.id, previewable])

  function handleDownload() {
    if (!version) return
    setDownloadError(null)
    getDownloadUrl(version.id, {
      onSuccess: (res) => window.open(res.url, '_blank', 'noopener,noreferrer'),
      onError: (err) => setDownloadError(apiErrorMessage(err)),
    })
  }

  if (!open || !document) return null

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="preview-drawer-title" className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-surface-deep/80" onClick={onClose} aria-hidden="true" />
      <div className="relative h-full w-full max-w-2xl bg-surface-raised border-l border-surface-border shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
        <div className="gradient-strip flex-none" aria-hidden="true" />

        <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-surface-border flex-none">
          <div className="min-w-0">
            <h2 id="preview-drawer-title" className="text-sm font-sans font-semibold text-text-primary truncate">
              {document.display_name}
            </h2>
            {version && (
              <p className="text-xs font-mono text-text-primary/40 mt-0.5">
                v{version.version_number} · {version.mime_type}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-none">
            <button
              type="button"
              onClick={handleDownload}
              disabled={!version || downloading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans text-text-primary/60 border border-surface-border rounded-md hover:bg-surface-base hover:text-text-primary disabled:opacity-40 transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron"
            >
              {downloading ? (
                <Loader2 size={13} className="animate-spin" aria-hidden="true" />
              ) : (
                <Download size={13} aria-hidden="true" />
              )}
              Download
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close preview"
              className="text-text-primary/40 hover:text-text-primary/70 transition-colors rounded p-1 focus-visible:ring-2 focus-visible:ring-accent-saffron"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        </div>

        {downloadError && (
          <p role="alert" className="text-xs font-sans text-accent-critical px-5 pt-3">
            {downloadError}
          </p>
        )}

        <div className="flex-1 overflow-auto p-5">
          {!version && (
            <div className="h-full flex flex-col items-center justify-center text-center gap-2">
              <FileX size={24} className="text-text-primary/20" aria-hidden="true" />
              <p className="text-sm font-sans text-text-primary/40">No version available to preview.</p>
            </div>
          )}

          {version && !previewable && (
            <div className="h-full flex flex-col items-center justify-center text-center gap-2">
              <FileWarning size={24} className="text-text-primary/20" aria-hidden="true" />
              <p className="text-sm font-sans text-text-primary/50">
                Preview is not supported for this file type ({version.mime_type}).
              </p>
              <p className="text-xs font-sans text-text-primary/30">Use Download to view this file.</p>
            </div>
          )}

          {version && previewable && previewLoading && (
            <div className="h-full flex items-center justify-center">
              <Loader2 size={20} className="animate-spin text-text-primary/30" aria-hidden="true" />
            </div>
          )}

          {version && previewable && !previewLoading && previewError && (
            <p role="alert" className="text-sm font-sans text-accent-critical text-center py-8">
              {previewError}
            </p>
          )}

          {version && previewable && !previewLoading && !previewError && previewUrl && (
            <>
              {previewKind === 'image' && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={previewUrl}
                  alt={document.display_name}
                  className="max-w-full max-h-full mx-auto rounded-md"
                />
              )}
              {(previewKind === 'pdf' || previewKind === 'text') && (
                <iframe
                  src={previewUrl}
                  title={document.display_name}
                  className="w-full h-full min-h-[70vh] rounded-md border border-surface-border bg-white"
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
