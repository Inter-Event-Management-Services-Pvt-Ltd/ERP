'use client'

import { use, useEffect, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, ChevronDown, Plus, Loader2, MapPin, FileText, Folder } from 'lucide-react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { EmptyState } from '@/components/states/empty-state'
import { useRooms, useLocations, useCreateLocation, useLocationContents } from '@/hooks/use-physical-archive'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import { buildLocationTree, locationDisplayName, type LocationTreeNode } from '@/lib/locations'
import { cn } from '@/lib/utils'
import type { PhysicalLocationType } from '@/types'

const LOCATION_TYPES: PhysicalLocationType[] = ['RACK', 'SHELF', 'CABINET', 'BOX', 'FILE_SLOT']

/** Required hierarchy: RACK -> SHELF -> CABINET -> BOX -> FILE_SLOT. RACK has no parent. */
const PARENT_TYPE: Record<PhysicalLocationType, PhysicalLocationType | null> = {
  RACK: null,
  SHELF: 'RACK',
  CABINET: 'SHELF',
  BOX: 'CABINET',
  FILE_SLOT: 'BOX',
}

const FILE_SLOT_HELP = 'Create Rack -> Shelf -> Cabinet -> Box before adding file slots.'

const locationSchema = z
  .object({
    code: z.string().min(1, 'Code is required').max(50),
    location_type: z.enum(['RACK', 'SHELF', 'CABINET', 'BOX', 'FILE_SLOT']),
    label: z.string().optional(),
    parent_location_id: z.string().optional(),
  })
  .superRefine((values, ctx) => {
    const requiredParentType = PARENT_TYPE[values.location_type]
    if (requiredParentType && !values.parent_location_id) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['parent_location_id'],
        message: `Select a parent ${requiredParentType} location`,
      })
    }
    if (!requiredParentType && values.parent_location_id) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['parent_location_id'],
        message: 'Racks sit at the top level and cannot have a parent location',
      })
    }
  })
type LocationFormValues = z.infer<typeof locationSchema>

interface Props {
  params: Promise<{ id: string }>
}

export default function RoomDetailPage({ params }: Props) {
  const { id: roomId } = use(params)
  const { data: user } = useMe()
  const { data: rooms = [], isLoading, error, refetch } = useRooms()
  const {
    data: locations = [],
    isLoading: locationsLoading,
    error: locationsError,
  } = useLocations(roomId)
  const { mutate: createLocation, isPending: creating } = useCreateLocation(roomId)

  const room = rooms.find((r) => r.id === roomId)

  const [showLocationForm, setShowLocationForm] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(null)

  const canManage = user?.isSuperUser || user?.permissions.includes('archive.manage')

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    control,
    formState: { errors },
  } = useForm<LocationFormValues>({
    resolver: zodResolver(locationSchema),
    defaultValues: { location_type: 'RACK', parent_location_id: '' },
  })

  const selectedType = useWatch({ control, name: 'location_type' })
  const requiredParentType = PARENT_TYPE[selectedType]

  const activeLocations = locations.filter((loc) => loc.is_active)
  const hasActive = (type: PhysicalLocationType) => activeLocations.some((loc) => loc.location_type === type)
  const hasActiveBox = hasActive('BOX')
  const parentOptions = requiredParentType
    ? activeLocations.filter((loc) => loc.location_type === requiredParentType)
    : []

  // Clear the parent selection whenever the chosen type (and therefore the required parent type) changes.
  useEffect(() => {
    setValue('parent_location_id', '')
  }, [selectedType, setValue])

  function onCreateLocation(values: LocationFormValues) {
    setLocationError(null)
    if (values.location_type === 'FILE_SLOT' && !hasActiveBox) {
      setLocationError('Create Rack -> Shelf -> Cabinet -> Box before adding file slots.')
      return
    }
    createLocation(
      {
        archive_room_id: roomId,
        parent_location_id: requiredParentType ? values.parent_location_id : undefined,
        code: values.code,
        location_type: values.location_type,
        label: values.label?.trim() || undefined,
      },
      {
        onSuccess: () => { reset({ location_type: 'RACK', parent_location_id: '' }); setShowLocationForm(false) },
        onError: (err) => setLocationError(apiErrorMessage(err)),
      }
    )
  }

  const tree = buildLocationTree(locations)

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
                    <label htmlFor="loc-code" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                      Code <span className="text-accent-critical">*</span>
                    </label>
                    <input
                      id="loc-code"
                      {...register('code')}
                      placeholder="e.g. A1"
                      className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
                    />
                    {errors.code && <p className="text-xs text-accent-critical mt-0.5">{errors.code.message}</p>}
                  </div>
                  <div>
                    <label htmlFor="loc-type" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                      Type <span className="text-accent-critical">*</span>
                    </label>
                    <select
                      id="loc-type"
                      {...register('location_type')}
                      className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
                    >
                      {LOCATION_TYPES.map((t) => (
                        <option key={t} value={t} disabled={t === 'FILE_SLOT' && !hasActiveBox}>
                          {t}
                        </option>
                      ))}
                    </select>
                    {selectedType === 'FILE_SLOT' && !hasActiveBox && (
                      <p className="text-xs font-sans text-text-primary/50 mt-1">{FILE_SLOT_HELP}</p>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="loc-label" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                      Label <span className="text-text-primary/30">(optional)</span>
                    </label>
                    <input
                      id="loc-label"
                      {...register('label')}
                      placeholder="e.g. Rack A1"
                      className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
                    />
                  </div>
                  {requiredParentType ? (
                    <div>
                      <label htmlFor="loc-parent" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                        Parent location ({requiredParentType}) <span className="text-accent-critical">*</span>
                      </label>
                      <select
                        id="loc-parent"
                        {...register('parent_location_id')}
                        className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
                      >
                        <option value="">Select a {requiredParentType.toLowerCase()}…</option>
                        {parentOptions.map((loc) => (
                          <option key={loc.id} value={loc.id}>
                            {locationDisplayName(loc)} ({loc.location_type})
                          </option>
                        ))}
                      </select>
                      {errors.parent_location_id && (
                        <p className="text-xs text-accent-critical mt-0.5">{errors.parent_location_id.message}</p>
                      )}
                      {parentOptions.length === 0 && (
                        <p className="text-xs font-sans text-text-primary/50 mt-1">
                          No active {requiredParentType.toLowerCase()} locations in this room yet — create one first.
                        </p>
                      )}
                    </div>
                  ) : (
                    <div>
                      <p className="text-xs font-sans text-text-primary/70 font-medium block mb-1">Parent location</p>
                      <p className="text-xs font-sans text-text-primary/40 rounded-md border border-surface-border bg-surface-base px-3 py-2">
                        Racks sit at the top level and have no parent location.
                      </p>
                    </div>
                  )}
                </div>
                {locationError && <p role="alert" className="text-xs text-accent-critical">{locationError}</p>}
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => { setShowLocationForm(false); reset({ location_type: 'RACK', parent_location_id: '' }); setLocationError(null) }}
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

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-4 space-y-3">
                <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
                  Locations
                </p>
                {locationsLoading && <SkeletonScreen rows={4} />}
                {!locationsLoading && locationsError && (
                  <p className="text-xs text-accent-critical font-sans">{apiErrorMessage(locationsError)}</p>
                )}
                {!locationsLoading && !locationsError && tree.length === 0 && (
                  <EmptyState heading="No locations yet" body="Add a rack, shelf or box to start organizing this room." />
                )}
                {!locationsLoading && !locationsError && tree.length > 0 && (
                  <ul className="space-y-0.5">
                    {tree.map((node) => (
                      <LocationTreeRow
                        key={node.id}
                        node={node}
                        depth={0}
                        selectedId={selectedLocationId}
                        onSelect={setSelectedLocationId}
                      />
                    ))}
                  </ul>
                )}
              </div>

              <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-4 space-y-3">
                <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
                  Contents
                </p>
                <LocationContentsPanel locationId={selectedLocationId} />
              </div>
            </div>
          </>
        )}
      </ContentArea>
    </AppShell>
  )
}

function LocationTreeRow({
  node,
  depth,
  selectedId,
  onSelect,
}: {
  node: LocationTreeNode
  depth: number
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = node.children.length > 0
  const isSelected = node.id === selectedId

  return (
    <li>
      <div
        className={cn(
          'flex items-center gap-1 rounded-md transition-colors duration-100',
          isSelected ? 'bg-accent-madder/30' : 'hover:bg-surface-deep/50'
        )}
        style={{ paddingLeft: `${depth * 1}rem` }}
      >
        {hasChildren ? (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-label={expanded ? `Collapse ${locationDisplayName(node)}` : `Expand ${locationDisplayName(node)}`}
            aria-expanded={expanded}
            className="flex-none p-1 text-text-primary/30 hover:text-text-primary/60 transition-colors"
          >
            {expanded ? <ChevronDown size={12} aria-hidden="true" /> : <ChevronRight size={12} aria-hidden="true" />}
          </button>
        ) : (
          <span className="flex-none w-[22px]" aria-hidden="true" />
        )}
        <button
          type="button"
          onClick={() => onSelect(node.id)}
          className="flex flex-1 min-w-0 items-center gap-1.5 py-1.5 pr-2 text-left text-sm font-sans text-text-primary/80 hover:text-text-primary transition-colors"
        >
          <Folder size={13} className="flex-none text-accent-saffron/70" aria-hidden="true" />
          <span className="truncate">{locationDisplayName(node)}</span>
          <span className="flex-none text-xs font-mono text-text-primary/30">{node.location_type}</span>
          {!node.is_active && (
            <span className="flex-none text-xs font-sans text-text-primary/30">(inactive)</span>
          )}
        </button>
      </div>
      {hasChildren && expanded && (
        <ul className="space-y-0.5">
          {node.children.map((child) => (
            <LocationTreeRow key={child.id} node={child} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} />
          ))}
        </ul>
      )}
    </li>
  )
}

function LocationContentsPanel({ locationId }: { locationId: string | null }) {
  const { data: contents, isLoading, error } = useLocationContents(locationId)

  if (!locationId) {
    return <p className="text-xs font-sans text-text-primary/30 py-2">Select a location to view its contents.</p>
  }

  if (isLoading) return <SkeletonScreen rows={3} />
  if (error) return <p className="text-xs text-accent-critical font-sans">{apiErrorMessage(error)}</p>
  if (!contents) return null

  return (
    <div className="space-y-3">
      <p className="text-xs font-sans text-text-primary/60">
        <span className="font-mono text-accent-saffron">{locationDisplayName(contents.location)}</span>{' '}
        ({contents.location.location_type}) — {contents.child_locations.length} sub-location
        {contents.child_locations.length !== 1 ? 's' : ''}, {contents.physical_files.length} file
        {contents.physical_files.length !== 1 ? 's' : ''}
      </p>

      {contents.physical_files.length === 0 ? (
        <p className="text-xs text-text-primary/30 font-sans py-2">No physical files in this location.</p>
      ) : (
        <ul className="space-y-1.5">
          {contents.physical_files.map((file) => (
            <li key={file.id}>
              <Link
                href={`/archive/files/${file.id}`}
                className="flex items-center justify-between rounded-md border border-surface-border bg-surface-base px-3 py-2 hover:bg-surface-raised transition-colors"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <FileText size={13} className="text-accent-saffron/60 flex-none" aria-hidden="true" />
                  <div className="min-w-0">
                    <p className="text-sm font-mono text-text-primary truncate">{file.physical_file_code}</p>
                    {file.notes && (
                      <p className="text-xs font-sans text-text-primary/40 truncate">{file.notes}</p>
                    )}
                  </div>
                </div>
                <span
                  className={cn(
                    'text-xs font-mono ml-2 flex-none',
                    file.status === 'CHECKED_OUT'
                      ? 'text-accent-warning'
                      : file.status === 'AVAILABLE'
                        ? 'text-green-400/70'
                        : file.status === 'MISSING'
                          ? 'text-accent-critical/80'
                          : 'text-text-primary/40'
                  )}
                >
                  {file.status}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
