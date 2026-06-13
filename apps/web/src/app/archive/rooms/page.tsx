'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Archive, ChevronRight, Plus, Loader2 } from 'lucide-react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { EmptyState } from '@/components/states/empty-state'
import { useRooms, useCreateRoom } from '@/hooks/use-physical-archive'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'

function deriveRoomCode(name: string): string {
  const words = name
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9\s]/g, '')
    .split(/\s+/)
    .filter(Boolean)
  if (words.length === 0) return ''
  if (words.length === 1) return words[0].slice(0, 12)
  return words.map((w) => w[0]).join('').slice(0, 12)
}

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  code: z.string().min(1),
  description: z.string().optional(),
})
type FormValues = z.infer<typeof schema>

export default function RoomsPage() {
  const { data: user } = useMe()
  const { data: rooms = [], isLoading, error, refetch } = useRooms()
  const { mutate: createRoom, isPending: creating } = useCreateRoom()
  const [showForm, setShowForm] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const canManage = user?.isSuperUser || user?.permissions.includes('archive.manage')

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    control,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const roomName = useWatch({ control, name: 'name', defaultValue: '' })
  useEffect(() => {
    setValue('code', deriveRoomCode(roomName), { shouldValidate: false })
  }, [roomName, setValue])

  function onSubmit(values: FormValues) {
    setCreateError(null)
    createRoom(values, {
      onSuccess: () => { reset(); setShowForm(false) },
      onError: (err) => setCreateError(apiErrorMessage(err)),
    })
  }

  return (
    <AppShell>
      <PageHeader
        title="Archive Rooms"
        subtitle="Physical storage rooms"
        actions={
          canManage ? (
            <button
              type="button"
              onClick={() => setShowForm((v) => !v)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans font-medium bg-accent-saffron text-surface-deep rounded-md hover:bg-accent-warning transition-colors"
            >
              <Plus size={13} aria-hidden="true" />
              New Room
            </button>
          ) : null
        }
      />

      <ContentArea>
        {showForm && canManage && (
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="rounded-lg border border-surface-border bg-surface-raised px-5 py-4 mb-5 space-y-3"
          >
            <p className="text-xs font-sans font-semibold text-text-primary/50 uppercase tracking-wider">
              New Room
            </p>
            <div>
              <label htmlFor="room-name" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                Name <span className="text-accent-critical">*</span>
              </label>
              <input
                id="room-name"
                {...register('name')}
                className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
              />
              {errors.name && <p className="text-xs text-accent-critical mt-0.5">{errors.name.message}</p>}
              {deriveRoomCode(roomName) && (
                <p className="text-xs font-mono text-text-primary/40 mt-1">
                  Code: <span className="text-accent-saffron/60">{deriveRoomCode(roomName)}</span>
                </p>
              )}
              <input type="hidden" {...register('code')} />
            </div>
            <div>
              <label htmlFor="room-desc" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                Description <span className="text-text-primary/30">(optional)</span>
              </label>
              <input
                id="room-desc"
                {...register('description')}
                className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
              />
            </div>
            {createError && <p role="alert" className="text-xs text-accent-critical">{createError}</p>}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => { setShowForm(false); reset(); setCreateError(null) }}
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
                Create Room
              </button>
            </div>
          </form>
        )}

        {isLoading && <SkeletonScreen rows={4} />}
        {!isLoading && error && <ErrorState message="Failed to load rooms." onRetry={() => refetch()} />}
        {!isLoading && !error && rooms.length === 0 && (
          <EmptyState heading="No rooms yet" body="Create the first archive room to get started." />
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
                    <Archive size={15} className="text-accent-saffron flex-none" aria-hidden="true" />
                    <div>
                      <p className="text-sm font-sans text-text-primary font-medium">{room.name}</p>
                      <p className="text-xs font-mono text-text-primary/40">{room.code}</p>
                      {room.description && (
                        <p className="text-xs font-sans text-text-primary/40 mt-0.5">{room.description}</p>
                      )}
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-text-primary/30 group-hover:text-text-primary/60 transition-colors" aria-hidden="true" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </ContentArea>
    </AppShell>
  )
}
