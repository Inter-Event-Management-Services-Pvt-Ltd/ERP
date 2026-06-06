'use client'

import { Archive, Download, Loader2, RefreshCw } from 'lucide-react'
import { useProjectExports, useCreateExport, useExportDownloadUrl } from '@/hooks/use-exports'
import { apiErrorMessage } from '@/lib/errors'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'
import type { ArchiveExport, ExportStatus } from '@/types'

const STATUS_LABEL: Record<ExportStatus, string> = {
  QUEUED: 'Queued',
  PROCESSING: 'Processing',
  READY: 'Ready',
  FAILED: 'Failed',
  EXPIRED: 'Expired',
}

const STATUS_CLASS: Record<ExportStatus, string> = {
  QUEUED: 'text-accent-warning',
  PROCESSING: 'text-accent-saffron',
  READY: 'text-green-400',
  FAILED: 'text-accent-critical',
  EXPIRED: 'text-text-primary/30',
}

interface ArchiveExportPanelProps {
  projectId: string
  canExport: boolean
}

export function ArchiveExportPanel({ projectId, canExport }: ArchiveExportPanelProps) {
  const { data: exports, isLoading, refetch } = useProjectExports(projectId)
  const { mutate: createExport, isPending: requesting, error: createError } = useCreateExport(projectId)
  const { mutate: getDownloadUrl, isPending: downloading } = useExportDownloadUrl()

  function handleExport() {
    createExport()
  }

  function handleDownload(exportId: string) {
    getDownloadUrl(exportId, {
      onSuccess: (res) => window.open(res.url, '_blank', 'noopener,noreferrer'),
    })
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
          Archive Export
        </p>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => refetch()}
            aria-label="Refresh export list"
            className="text-text-primary/20 hover:text-text-primary/50 transition-colors p-0.5 rounded"
          >
            <RefreshCw size={11} aria-hidden="true" />
          </button>
          {canExport && (
            <button
              type="button"
              onClick={handleExport}
              disabled={requesting}
              className="flex items-center gap-1 text-xs font-sans text-accent-saffron/70 hover:text-accent-saffron transition-colors disabled:opacity-40"
            >
              {requesting ? (
                <Loader2 size={11} className="animate-spin" aria-hidden="true" />
              ) : (
                <Archive size={11} aria-hidden="true" />
              )}
              Export ZIP
            </button>
          )}
        </div>
      </div>

      {createError && (
        <p role="alert" className="text-xs text-accent-critical font-sans">
          {apiErrorMessage(createError)}
        </p>
      )}

      {isLoading && (
        <div className="space-y-1">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-8 rounded bg-surface-border/30 shimmer" />
          ))}
        </div>
      )}

      {!isLoading && exports.length === 0 && (
        <p className="text-xs font-sans text-text-primary/30 py-1">No exports yet.</p>
      )}

      {!isLoading && exports.length > 0 && (
        <ul className="space-y-1">
          {exports.map((exp) => (
            <ExportRow
              key={exp.id}
              exp={exp}
              onDownload={() => handleDownload(exp.id)}
              downloading={downloading}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function ExportRow({
  exp,
  onDownload,
  downloading,
}: {
  exp: ArchiveExport
  onDownload: () => void
  downloading: boolean
}) {
  const isActive = exp.status === 'QUEUED' || exp.status === 'PROCESSING'

  return (
    <li className="flex items-center justify-between rounded px-2 py-1.5 bg-surface-deep/40 border border-surface-border/50">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          {isActive && (
            <Loader2 size={10} className="animate-spin text-accent-saffron/60 flex-none" aria-hidden="true" />
          )}
          <span className={cn('text-xs font-mono font-semibold', STATUS_CLASS[exp.status])}>
            {STATUS_LABEL[exp.status]}
          </span>
        </div>
        <p className="text-xs font-mono text-text-primary/30 leading-tight">
          {format(new Date(exp.requested_at), 'dd MMM yyyy HH:mm')}
        </p>
      </div>

      {exp.status === 'READY' && (
        <button
          type="button"
          onClick={onDownload}
          disabled={downloading}
          aria-label="Download export ZIP"
          className="ml-2 flex-none text-text-primary/30 hover:text-accent-saffron transition-colors disabled:opacity-40"
        >
          {downloading ? (
            <Loader2 size={12} className="animate-spin" aria-hidden="true" />
          ) : (
            <Download size={12} aria-hidden="true" />
          )}
        </button>
      )}
    </li>
  )
}
