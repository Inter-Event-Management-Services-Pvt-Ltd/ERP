'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, Plus, Loader2, MapPin, FileText } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { useRooms, useCreateLocation, useLocationContents } from '@/hooks/use-physical-archive'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import type { PhysicalLocationType } from '@/types'

const LOCATION_TYPES: PhysicalLocationType[] = ['RACK', 'SHELF', 'CABINET', 'BOX', 'FILE_SLOT']

const locationSchema = z.object({
  label: z.string().min(1, 'Label is required').max(50),
  type: z.enum(['RACK', 'SHELF', 'CABINET', 'BOX', 'FILE_SLOT']),
  description: z.string().optional(),
})
type LocationFormValues = z.infer<typeof locationSchema>

interface Props {
  params: Promise<{ id: string }>
}

export default function RoomDetailPage({ params }: Props) {
  const { id: roomId } = use(params)
  const { data: user } = useMe()
  const { data: rooms = [], isLoading, error, refetch } = useRooms()
  const { mutate: createLocation, isPending: creating } = useCreateLocation()

  const room = rooms.find((r) => r.id === roomId)

  const [showLocationForm, setShowLocationForm] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)
  const [browseLocationId, setBrowseLocationId] = useState('')

  const canManage = user?.isSuperUser || user?.permissions.includes('archive.manage')

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<LocationFormValues>({
    resolver: zodResolver(locationSchema),
    defaultValues: { type: 'RACK' },
  })

  function onCreateLocation(values: LocationFormValues) {
    setLocationError(null)
    createLocation(
      {
        room_id: roomId,
        label: values.label,
        type: values.type,
        description: values.description,
      },
      {
        onSuccess: () => { reset(); setShowLocationForm(false) },
        onError: (err) => setLocationError(apiErrorMessage(err)),
      }
    )
  }

  return (
    <AppShell>
      <PageHeader
        title={room?.name ?? 'Room'}
        subtitle={
          <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-text-primary/40 font-sans">
            <Link href="/archive/rooms" className="hover:text-text-primary/70 transition-colors">
              Rooms
            </Link>
            <ChevronRight size={12} aria-hidden="true" />
            <span className="text-text-primary/60">{room?.name ?? roomId}</span>
          </nav>
        }
        actions={
          canManage ? (
            <button
              type="button"
              onClick={() => setShowLocationForm((v) => !v)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans font-medium bg-accent-saffron text-surface-deep rounded-md hover:bg-accent-warning transition-colors"
            >
              <Plus size={13} aria-hidden="true" />
              Add Location
            </button>
          ) : null
        }
      />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={4} />}
        {!isLoading && error && <ErrorState message="Failed to load room." onRetry={() => refetch()} />}

        {!isLoading && !error && (
          <>
            {room && (
              <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3 mb-5">
                <div className="flex items-center gap-3">
                  <MapPin size={14} className="text-accent-saffron" aria-hidden="true" />
                  <div>
                    <p className="text-sm font-sans text-text-primary font-medium">{room.name}</p>
                    <p className="text-xs font-mono text-text-primary/40">{room.code}</p>
                    {room.description && (
                      <p className="text-xs font-sans text-text-primary/50 mt-0.5">{room.description}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {showLocationForm && canManage && (
              <form
                onSubmit={handleSubmit(onCreateLocation)}
                className="rounded-lg border border-surface-border bg-surface-raised px-5 py-4 mb-5 space-y-3"
              >
                <p className="text-xs font-sans font-semibold text-text-primary/50 uppercase tracking-wider">
                  Add Location
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="loc-label" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                      Label <span className="text-accent-critical">*</span>
                    </label>
                    <input
                      id="loc-label"
                      {...register('label')}
                      placeholder="e.g. Rack A1"
                      className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
                    />
                    {errors.label && <p className="text-xs text-accent-critical mt-0.5">{errors.label.message}</p>}
                  </div>
                  <div>
                    <label htmlFor="loc-type" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                      Type <span className="text-accent-critical">*</span>
                    </label>
                    <select
                      id="loc-type"
                      {...register('type')}
                      className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
                    >
                      {LOCATION_TYPES.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label htmlFor="loc-desc" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                    Description <span className="text-text-primary/30">(optional)</span>
                  </label>
                  <input
                    id="loc-desc"
                    {...register('description')}
                    className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
                  />
                </div>
                {locationError && <p role="alert" className="text-xs text-accent-critical">{locationError}</p>}
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => { setShowLocationForm(false); reset(); setLocationError(null) }}
                    className="text-xs font-sans text-text-primary/50 hover:text-text-primary/80 px-3 py-1.5 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creating}
                    className="flex items-center gap-1.5 text-xs font-sans font-medium px-4 py-1.5 rounded-md bg-accent-saffron/90 text-surface-deep hover:bg-accent-saffron disabled:opacity-40 transition-colors"
                  >
                    {creating && <Loader2 size={11} className="animate-spin" aria-hidden="true" />}
                    Add
                  </button>
                </div>
              </form>
            )}

            {/* Location content browser — requires a known location ID */}
            <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-4 space-y-3">
              <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
                Browse Location Contents
              </p>
              <p className="text-xs font-sans text-text-primary/40">
                Enter a location ID to view its physical files.{' '}
                <span className="text-accent-warning">
                  (OPEN-027: listing locations by room is not yet supported by the API)
                </span>
              </p>
              <LocationBrowser />
            </div>
          </>
        )}
      </ContentArea>
    </AppShell>
  )
}

function LocationBrowser() {
  const [locationId, setLocationId] = useState('')
  const [submitted, setSubmitted] = useState('')
  const { data: contents, isLoading, error } = useLocationContents(submitted || null)

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input
          type="text"
          value={locationId}
          onChange={(e) => setLocationId(e.target.value)}
          placeholder="Location UUID"
          className="flex-1 rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-primary/30 focus:outline-none focus:ring-2 focus:ring-accent-saffron"
        />
        <button
          type="button"
          onClick={() => setSubmitted(locationId.trim())}
          disabled={!locationId.trim()}
          className="px-3 py-1.5 text-xs font-sans rounded-md bg-surface-border text-text-primary/60 hover:text-text-primary hover:bg-surface-border/70 disabled:opacity-40 transition-colors"
        >
          View
        </button>
      </div>

      {submitted && isLoading && <SkeletonScreen rows={3} />}
      {submitted && !isLoading && error && (
        <p className="text-xs text-accent-critical font-sans">{apiErrorMessage(error)}</p>
      )}
      {submitted && !isLoading && !error && contents && (
        <div className="space-y-2">
          <p className="text-xs font-sans text-text-primary/60">
            <span className="font-mono text-accent-saffron">{contents.location.label}</span>{' '}
            ({contents.location.type}) — {contents.files.length} file{contents.files.length !== 1 ? 's' : ''}
          </p>
          {contents.files.length === 0 ? (
            <p className="text-xs text-text-primary/30 font-sans py-2">No physical files in this location.</p>
          ) : (
            <ul className="space-y-1.5">
              {contents.files.map((file) => (
                <li key={file.id}>
                  <Link
                    href={`/archive/files/${file.id}`}
                    className="flex items-center justify-between rounded-md border border-surface-border bg-surface-base px-3 py-2 hover:bg-surface-raised transition-colors"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText size={13} className="text-accent-saffron/60 flex-none" aria-hidden="true" />
                      <div className="min-w-0">
                        <p className="text-sm font-mono text-text-primary truncate">{file.file_code}</p>
                        {file.description && (
                          <p className="text-xs font-sans text-text-primary/40 truncate">{file.description}</p>
                        )}
                      </div>
                    </div>
                    <span className={`text-xs font-mono ml-2 flex-none ${file.state === 'CHECKED_OUT' ? 'text-accent-warning' : file.state === 'IN_STORAGE' ? 'text-green-400/70' : 'text-text-primary/40'}`}>
                      {file.state}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
