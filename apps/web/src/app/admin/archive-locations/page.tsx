'use client'

import { useState } from 'react'
import { Archive, ChevronDown, ChevronRight } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { useRooms, useLocations } from '@/hooks/use-physical-archive'
import { useUpdatePhysicalRoom, useUpdatePhysicalLocation } from '@/hooks/use-admin'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import type { PhysicalRoom, PhysicalLocation, UpdatePhysicalRoomPayload, UpdatePhysicalLocationPayload } from '@/types'

const inputCls = 'px-3 py-2 text-sm bg-surface-base border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50'
const labelCls = 'text-xs font-semibold text-text-primary/60 uppercase tracking-wide'

function RoomEditForm({
  room,
  onDone,
}: {
  room: PhysicalRoom
  onDone: () => void
}) {
  const mutation = useUpdatePhysicalRoom()
  const [form, setForm] = useState<UpdatePhysicalRoomPayload>({
    code: room.code,
    name: room.name,
    description: room.description ?? undefined,
    is_active: room.is_active,
  })
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await mutation.mutateAsync({ id: room.id, payload: form })
      onDone()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-3 p-3 bg-surface-base border border-surface-border rounded-lg">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label className={labelCls}>Code</label>
          <input className={inputCls} value={form.code ?? ''} onChange={(e) => setForm(f => ({ ...f, code: e.target.value }))} />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className={labelCls}>Name</label>
          <input className={inputCls} value={form.name ?? ''} onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))} />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <label className={labelCls}>Description</label>
        <input className={inputCls} value={form.description ?? ''} onChange={(e) => setForm(f => ({ ...f, description: e.target.value || undefined }))} placeholder="Optional" />
      </div>
      <div className="flex items-center gap-3">
        <input type="checkbox" id={`room-active-${room.id}`} checked={form.is_active ?? true} onChange={(e) => setForm(f => ({ ...f, is_active: e.target.checked }))} className="accent-accent-saffron" />
        <label htmlFor={`room-active-${room.id}`} className={labelCls}>Active</label>
      </div>
      {error && <p role="alert" className="text-xs text-accent-critical">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={mutation.isPending} className="px-3 py-1.5 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
          {mutation.isPending ? 'Saving…' : 'Save Room'}
        </button>
        <button type="button" onClick={onDone} className="px-3 py-1.5 text-xs text-text-primary/50 hover:text-text-primary transition-colors">Cancel</button>
      </div>
    </form>
  )
}

function LocationEditForm({
  location,
  onDone,
}: {
  location: PhysicalLocation
  onDone: () => void
}) {
  const mutation = useUpdatePhysicalLocation()
  const [form, setForm] = useState<UpdatePhysicalLocationPayload>({
    code: location.code,
    label: location.label ?? undefined,
    is_active: location.is_active,
  })
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await mutation.mutateAsync({ id: location.id, payload: form })
      onDone()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-2 flex flex-col gap-2 p-3 bg-surface-base border border-surface-border rounded-lg">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <div className="flex flex-col gap-1">
          <label className={labelCls}>Code</label>
          <input className={inputCls} value={form.code ?? ''} onChange={(e) => setForm(f => ({ ...f, code: e.target.value }))} />
        </div>
        <div className="flex flex-col gap-1">
          <label className={labelCls}>Label</label>
          <input className={inputCls} value={form.label ?? ''} onChange={(e) => setForm(f => ({ ...f, label: e.target.value }))} />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <input type="checkbox" id={`loc-active-${location.id}`} checked={form.is_active ?? true} onChange={(e) => setForm(f => ({ ...f, is_active: e.target.checked }))} className="accent-accent-saffron" />
        <label htmlFor={`loc-active-${location.id}`} className={labelCls}>Active</label>
      </div>
      {error && <p role="alert" className="text-xs text-accent-critical">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={mutation.isPending} className="px-3 py-1.5 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
          {mutation.isPending ? 'Saving…' : 'Save'}
        </button>
        <button type="button" onClick={onDone} className="px-3 py-1.5 text-xs text-text-primary/50 hover:text-text-primary transition-colors">Cancel</button>
      </div>
    </form>
  )
}

function RoomRow({ room, canManage }: { room: PhysicalRoom; canManage: boolean }) {
  const [expanded, setExpanded] = useState(false)
  const [editingRoom, setEditingRoom] = useState(false)
  const [editingLocationId, setEditingLocationId] = useState<string | null>(null)

  const { data: locations = [], isLoading } = useLocations(expanded ? room.id : '')

  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <button
            type="button"
            onClick={() => setExpanded((x) => !x)}
            aria-expanded={expanded}
            aria-label={expanded ? 'Collapse room' : 'Expand room'}
            className="text-text-primary/30 hover:text-accent-saffron transition-colors"
          >
            {expanded ? <ChevronDown size={14} aria-hidden="true" /> : <ChevronRight size={14} aria-hidden="true" />}
          </button>
          <span className="font-mono text-xs text-text-primary/40 mr-1">{room.code}</span>
          <span className="font-medium text-text-primary/85">{room.name}</span>
          {!room.is_active && <Badge variant="archived">Inactive</Badge>}
        </div>
        {canManage && !editingRoom && (
          <button type="button" onClick={() => setEditingRoom(true)} className="text-xs text-text-primary/40 hover:text-accent-saffron transition-colors flex-none">Edit</button>
        )}
      </div>

      {editingRoom && (
        <RoomEditForm room={room} onDone={() => setEditingRoom(false)} />
      )}

      {expanded && !editingRoom && (
        <div className="mt-4 ml-5 flex flex-col gap-2">
          {isLoading && <p className="text-xs text-text-primary/30 font-mono">Loading locations…</p>}
          {!isLoading && locations.length === 0 && (
            <p className="text-xs text-text-primary/30 font-sans">No locations in this room.</p>
          )}
          {locations.map((loc: PhysicalLocation) => (
            <div key={loc.id} className="rounded border border-surface-border bg-surface-base p-3">
              {editingLocationId !== loc.id ? (
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs text-text-primary/40">{loc.code}</span>
                    <span className="text-sm text-text-primary/75">{loc.label}</span>
                    <span className="text-xs text-text-primary/30 font-mono">{loc.location_type}</span>
                    {!loc.is_active && <Badge variant="archived">Inactive</Badge>}
                  </div>
                  {canManage && (
                    <button type="button" onClick={() => setEditingLocationId(loc.id)} className="text-xs text-text-primary/40 hover:text-accent-saffron transition-colors flex-none">Edit</button>
                  )}
                </div>
              ) : (
                <LocationEditForm location={loc} onDone={() => setEditingLocationId(null)} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function AdminArchiveLocationsPage() {
  const { data: user } = useMe()
  const { data: rooms = [], isLoading, error, refetch } = useRooms()
  const canManage = (user?.isSuperUser ?? false) || (user?.permissions.includes('archive.manage') ?? false)

  return (
    <AppShell>
      <PageHeader title="Archive Locations" subtitle="Rooms and physical location management" />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={5} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && rooms.length === 0 && (
          <EmptyState icon={Archive} heading="No archive rooms" body="Archive rooms are managed in the Archive module." />
        )}

        {!isLoading && !error && rooms.length > 0 && (
          <div className="flex flex-col gap-3">
            {rooms.map((room: PhysicalRoom) => (
              <RoomRow key={room.id} room={room} canManage={canManage} />
            ))}
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
