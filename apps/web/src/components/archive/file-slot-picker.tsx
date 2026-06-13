'use client'

import { useEffect, useState } from 'react'
import { useRooms, useLocations } from '@/hooks/use-physical-archive'
import { locationPath } from '@/lib/locations'

interface FileSlotPickerProps {
  roomId?: string | null
  value: string | null
  onChange: (locationId: string | null) => void
}

export function FileSlotPicker({ roomId: initialRoomId, value, onChange }: FileSlotPickerProps) {
  const { data: rooms = [] } = useRooms()
  const [roomId, setRoomId] = useState(initialRoomId ?? '')

  useEffect(() => {
    if (initialRoomId && !roomId) setRoomId(initialRoomId)
  }, [initialRoomId, roomId])

  const { data: locations = [], isLoading } = useLocations(roomId)
  const fileSlots = locations.filter((loc) => loc.location_type === 'FILE_SLOT' && loc.is_active)

  function handleRoomChange(next: string) {
    setRoomId(next)
    onChange(null)
  }

  return (
    <div className="space-y-2">
      <select
        aria-label="Archive room"
        value={roomId}
        onChange={(e) => handleRoomChange(e.target.value)}
        className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
      >
        <option value="">Select a room…</option>
        {rooms.map((room) => (
          <option key={room.id} value={room.id}>{room.name}</option>
        ))}
      </select>

      {roomId && (
        <select
          aria-label="File slot location"
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value || null)}
          disabled={isLoading}
          className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron disabled:opacity-40"
        >
          <option value="">{isLoading ? 'Loading…' : 'Select a file slot…'}</option>
          {fileSlots.map((loc) => (
            <option key={loc.id} value={loc.id}>{locationPath(loc, locations)}</option>
          ))}
        </select>
      )}

      {roomId && !isLoading && fileSlots.length === 0 && (
        <p className="text-xs font-sans text-text-primary/30">No file slots found in this room.</p>
      )}
    </div>
  )
}
