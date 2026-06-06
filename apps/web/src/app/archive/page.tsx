'use client'

import Link from 'next/link'
import { Archive, ChevronRight } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { EmptyState } from '@/components/states/empty-state'
import { useRooms } from '@/hooks/use-physical-archive'

export default function ArchivePage() {
  const { data: rooms = [], isLoading, error, refetch } = useRooms()

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
