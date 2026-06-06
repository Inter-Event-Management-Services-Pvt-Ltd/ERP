'use client'

import { useRef, useState } from 'react'
import { X, Upload, Loader2, FileText } from 'lucide-react'
import { useUploadDocument } from '@/hooks/use-documents'
import { apiErrorMessage } from '@/lib/errors'
import { cn } from '@/lib/utils'

interface DocumentUploadDialogProps {
  open: boolean
  folderId: string
  folderName: string
  onClose: () => void
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function DocumentUploadDialog({
  open,
  folderId,
  folderName,
  onClose,
}: DocumentUploadDialogProps) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [displayName, setDisplayName] = useState('')
  const [confidentialityLevelId, setConfidentialityLevelId] = useState('')
  const [documentTypeId, setDocumentTypeId] = useState('')
  const [changeNote, setChangeNote] = useState('')
  const [error, setError] = useState<string | null>(null)

  const { mutate: upload, isPending } = useUploadDocument(folderId)

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null
    setFile(f)
    if (f && !displayName) setDisplayName(f.name)
    setError(null)
  }

  function handleClose() {
    setFile(null)
    setDisplayName('')
    setConfidentialityLevelId('')
    setDocumentTypeId('')
    setChangeNote('')
    setError(null)
    onClose()
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) { setError('Select a file to upload.'); return }
    if (!confidentialityLevelId.trim()) {
      setError('Confidentiality level ID is required.')
      return
    }

    const fd = new FormData()
    fd.append('file', file)
    fd.append('confidentiality_level_id', confidentialityLevelId.trim())
    if (displayName.trim()) fd.append('display_name', displayName.trim())
    if (documentTypeId.trim()) fd.append('document_type_id', documentTypeId.trim())
    if (changeNote.trim()) fd.append('change_note', changeNote.trim())

    setError(null)
    upload(fd, {
      onSuccess: handleClose,
      onError: (err) => setError(apiErrorMessage(err)),
    })
  }

  if (!open) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="upload-doc-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div className="absolute inset-0 bg-surface-deep/80" onClick={handleClose} aria-hidden="true" />
      <div className="relative w-full max-w-md rounded-xl bg-surface-raised border border-surface-border shadow-2xl animate-in fade-in-0 zoom-in-95 duration-180">
        <div className="gradient-strip flex-none rounded-t-xl" aria-hidden="true" />

        <div className="px-6 pt-5 pb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 id="upload-doc-title" className="text-sm font-sans font-semibold text-text-primary">
              Upload to{' '}
              <span className="text-accent-saffron font-mono">{folderName}</span>
            </h2>
            <button
              onClick={handleClose}
              aria-label="Close dialog"
              className="text-text-primary/40 hover:text-text-primary/70 transition-colors rounded focus-visible:ring-2 focus-visible:ring-accent-saffron"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* File picker */}
            <div>
              <input
                ref={fileRef}
                type="file"
                id="upload-file"
                onChange={handleFileChange}
                className="sr-only"
                aria-label="Select file"
              />
              <label
                htmlFor="upload-file"
                className={cn(
                  'flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-6 cursor-pointer transition-colors',
                  file
                    ? 'border-accent-saffron/40 bg-accent-saffron/5'
                    : 'border-surface-border hover:border-accent-saffron/30 hover:bg-surface-base'
                )}
              >
                {file ? (
                  <>
                    <FileText size={20} className="text-accent-saffron" aria-hidden="true" />
                    <p className="text-sm font-sans text-text-primary text-center truncate max-w-xs">
                      {file.name}
                    </p>
                    <p className="text-xs font-mono text-text-primary/40">
                      {formatBytes(file.size)}
                    </p>
                  </>
                ) : (
                  <>
                    <Upload size={20} className="text-text-primary/30" aria-hidden="true" />
                    <p className="text-sm font-sans text-text-primary/50">
                      Click to select a file
                    </p>
                  </>
                )}
              </label>
            </div>

            {/* Display name */}
            <div>
              <label
                htmlFor="upload-display-name"
                className="text-xs font-sans text-text-primary/70 font-medium block mb-1"
              >
                Display name <span className="text-text-primary/30">(optional)</span>
              </label>
              <input
                id="upload-display-name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Defaults to file name"
                className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary placeholder:text-text-primary/30 focus:outline-none focus:ring-2 focus:ring-accent-saffron"
              />
            </div>

            {/* Confidentiality level */}
            <div>
              <label
                htmlFor="upload-confidentiality"
                className="text-xs font-sans text-text-primary/70 font-medium block mb-1"
              >
                Confidentiality level ID{' '}
                <span className="text-accent-critical">*</span>
              </label>
              <input
                id="upload-confidentiality"
                type="text"
                value={confidentialityLevelId}
                onChange={(e) => setConfidentialityLevelId(e.target.value)}
                placeholder="UUID — see OPEN-026 for lookup endpoint"
                className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-primary/20 focus:outline-none focus:ring-2 focus:ring-accent-saffron"
              />
              <p className="text-xs text-text-primary/30 font-sans mt-0.5">
                Lookup endpoint pending (OPEN-026)
              </p>
            </div>

            {/* Document type */}
            <div>
              <label
                htmlFor="upload-doc-type"
                className="text-xs font-sans text-text-primary/70 font-medium block mb-1"
              >
                Document type ID <span className="text-text-primary/30">(optional)</span>
              </label>
              <input
                id="upload-doc-type"
                type="text"
                value={documentTypeId}
                onChange={(e) => setDocumentTypeId(e.target.value)}
                placeholder="UUID — see OPEN-026 for lookup endpoint"
                className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-primary/20 focus:outline-none focus:ring-2 focus:ring-accent-saffron"
              />
            </div>

            {/* Change note */}
            <div>
              <label
                htmlFor="upload-change-note"
                className="text-xs font-sans text-text-primary/70 font-medium block mb-1"
              >
                Change note <span className="text-text-primary/30">(optional)</span>
              </label>
              <input
                id="upload-change-note"
                type="text"
                value={changeNote}
                onChange={(e) => setChangeNote(e.target.value)}
                placeholder="Brief description of the upload"
                className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary placeholder:text-text-primary/30 focus:outline-none focus:ring-2 focus:ring-accent-saffron"
              />
            </div>

            {error && (
              <p role="alert" className="text-xs font-sans text-accent-critical">
                {error}
              </p>
            )}

            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={handleClose}
                className="text-xs font-sans text-text-primary/50 hover:text-text-primary/80 px-3 py-1.5 rounded-md transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isPending || !file}
                className="flex items-center gap-1.5 text-xs font-sans font-medium px-4 py-1.5 rounded-md bg-accent-saffron/90 text-surface-deep hover:bg-accent-saffron disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {isPending && <Loader2 size={11} className="animate-spin" aria-hidden="true" />}
                Upload
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
