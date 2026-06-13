'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Archive, ChevronRight, ScanLine } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { EmptyState } from '@/components/states/empty-state'
import { useRooms } from '@/hooks/use-physical-archive'

export default function ArchivePage() {
  const router = useRouter()
  const { data: rooms = [], isLoading, error, refetch } = useRooms()
  const [scanToken, setScanToken] = useState('')

  function handleScanLookup(e: React.FormEvent) {
    e.preventDefault()
    const token = scanToken.trim()
    if (token) router.push(`/archive/scan/${encodeURIComponent(token)}`)
  }

  return (
    <AppShell>
      <PageHeader
        title="Physical Archive"
        subtitle="Storage rooms and physical files"
        actions={
          <Link
            href="/archive/rooms"
            className="text-xs font-sans text-accent-saffron/70 hover:text-accent-saffron transition-colors"
          >
            Manage rooms →
          </Link>
        }
      />

      <ContentArea>
        <form
          onSubmit={handleScanLookup}
          className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3 mb-5 flex flex-col sm:flex-row sm:items-end gap-3"
        >
          <div className="flex-1">
            <label htmlFor="scan-token" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
              Look up a label by QR token
            </label>
            <input
              id="scan-token"
              value={scanToken}
              onChange={(e) => setScanToken(e.target.value)}
              placeholder="Paste or scan the QR token"
              className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-primary/30 focus:outline-none focus:ring-2 focus:ring-accent-saffron"
            />
          </div>
          <button
            type="submit"
            disabled={!scanToken.trim()}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-sans font-medium bg-accent-saffron text-surface-deep rounded-md hover:bg-accent-warning disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron"
          >
            <ScanLine size={14} aria-hidden="true" />
            Find File
          </button>
        </form>

        {isLoading && <SkeletonScreen rows={4} />}

        {!isLoading && error && (
          <ErrorState
            message="Failed to load archive rooms."
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && rooms.length === 0 && (
          <EmptyState
            heading="No archive rooms"
            body="Archive rooms haven't been set up yet. Go to Manage Rooms to add one."
          />
        )}

        {!isLoading && !error && rooms.length > 0 && (
          <ul className="space-y-2">
            {rooms.map((room) => (
              <li key={room.id}>
                <Link
                  href={`/archive/rooms/${room.id}`}
                  className="flex items-center justify-between rounded-lg border border-surface-border bg-surface-raised px-4 py-3 hover:bg-surface-deep/50 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <Archive size={16} className="text-accent-saffron flex-none" aria-hidden="true" />
                    <div>
                      <p className="text-sm font-sans text-text-primary font-medium">{room.name}</p>
                      <p className="text-xs font-mono text-text-primary/40">{room.code}</p>
                    </div>
                  </div>
                  <ChevronRight
                    size={14}
                    className="text-text-primary/30 group-hover:text-text-primary/60 transition-colors"
                    aria-hidden="true"
                  />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </ContentArea>
    </AppShell>
  )
}
