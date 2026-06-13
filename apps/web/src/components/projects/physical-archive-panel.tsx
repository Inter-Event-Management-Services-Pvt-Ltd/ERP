'use client'

import Link from 'next/link'
import { Boxes, FileText, ChevronRight, RefreshCw } from 'lucide-react'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { useProjectPhysicalFiles } from '@/hooks/use-physical-archive'
import { apiErrorMessage } from '@/lib/errors'
import { locationDisplayName } from '@/lib/locations'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'
import type { PhysicalFileState } from '@/types'

const STATE_LABEL: Record<PhysicalFileState, string> = {
  AVAILABLE: 'Available',
  CHECKED_OUT: 'Checked Out',
  MISSING: 'Missing',
  UNDER_VERIFICATION: 'Under Verification',
  ARCHIVED: 'Archived',
}

const STATE_CLASS: Record<PhysicalFileState, string> = {
  AVAILABLE: 'text-green-400',
  CHECKED_OUT: 'text-accent-warning',
  MISSING: 'text-accent-critical',
  UNDER_VERIFICATION: 'text-accent-saffron',
  ARCHIVED: 'text-text-primary/30',
}

interface PhysicalArchivePanelProps {
  projectId: string
}

export function PhysicalArchivePanel({ projectId }: PhysicalArchivePanelProps) {
  const { data: files = [], isLoading, error, refetch } = useProjectPhysicalFiles(projectId)

  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Boxes size={14} className="text-accent-saffron" aria-hidden="true" />
          <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
            Physical Archive
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          aria-label="Refresh physical archive files"
          className="text-text-primary/30 hover:text-text-primary/60 transition-colors p-1 rounded"
        >
          <RefreshCw size={13} aria-hidden="true" />
        </button>
      </div>

      {isLoading && <SkeletonScreen rows={3} />}

      {!isLoading && error && (
        <p role="alert" className="text-sm font-sans text-accent-critical py-2">
          {apiErrorMessage(error)}
        </p>
      )}

      {!isLoading && !error && files.length === 0 && (
        <div className="py-6 text-center">
          <FileText size={20} className="text-text-primary/20 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm font-sans text-text-primary/40">
            No physical files archived for this project.
          </p>
        </div>
      )}

      {!isLoading && !error && files.length > 0 && (
        <ul className="space-y-1.5">
          {files.map((file) => (
            <li key={file.id}>
              <Link
                href={`/archive/files/${file.id}`}
                className="flex items-center justify-between gap-3 rounded-md border border-surface-border bg-surface-base px-3 py-2.5 hover:bg-surface-deep/50 transition-colors group"
              >
                <div className="flex items-start gap-2.5 min-w-0">
                  <FileText size={14} className="flex-none text-accent-saffron/70 mt-0.5" aria-hidden="true" />
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-mono text-text-primary">{file.physical_file_code}</p>
                      <span className={cn('text-xs font-sans font-medium', STATE_CLASS[file.status])}>
                        {STATE_LABEL[file.status]}
                      </span>
                    </div>
                    <p className="text-xs font-sans text-text-primary/40 mt-0.5">
                      Volume {file.volume_number}
                      {file.archive_room && <> · {file.archive_room.name}</>}
                      {file.archive_location && <> · {locationDisplayName(file.archive_location)}</>}
                    </p>
                    <p className="text-xs font-sans text-text-primary/30 mt-0.5">
                      {file.archived_on && (
                        <>Archived {format(new Date(file.archived_on), 'dd MMM yyyy')}</>
                      )}
                      {file.last_verified_at && (
                        <> · Last verified {format(new Date(file.last_verified_at), 'dd MMM yyyy')}</>
                      )}
                      {file.open_checkout && (
                        <span className="text-accent-warning"> · Checked out</span>
                      )}
                    </p>
                  </div>
                </div>
                <ChevronRight
                  size={14}
                  className="flex-none text-text-primary/30 group-hover:text-text-primary/60 transition-colors"
                  aria-hidden="true"
                />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
