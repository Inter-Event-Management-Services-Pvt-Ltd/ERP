'use client'

import { useState } from 'react'
import { X, PowerOff, Plus } from 'lucide-react'
import { ConfirmDialog } from '@/components/status/confirm-dialog'
import { useClients, useDeactivateClient } from '@/hooks/use-clients'
import { cn } from '@/lib/utils'
import type { Client } from '@/types'

interface ManageClientsDialogProps {
  open: boolean
  onClose: () => void
  onNewClient: () => void
}

export function ManageClientsDialog({ open, onClose, onNewClient }: ManageClientsDialogProps) {
  const { data: clients = [] } = useClients()
  const { mutate: deactivate, isPending } = useDeactivateClient()
  const [pendingId, setPendingId] = useState<string | null>(null)

  if (!open) return null

  const active = clients.filter((c) => c.is_active)
  const inactive = clients.filter((c) => !c.is_active)
  const target = pendingId ? clients.find((c) => c.id === pendingId) : null

  function handleConfirm() {
    if (!pendingId) return
    deactivate(pendingId, { onSuccess: () => setPendingId(null) })
  }

  return (
    <>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="manage-clients-title"
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div
          className="absolute inset-0 bg-surface-deep/80"
          onClick={onClose}
          aria-hidden="true"
        />
        <div className="relative w-full max-w-lg rounded-xl bg-surface-raised border border-surface-border shadow-2xl animate-in fade-in-0 zoom-in-95 duration-180 max-h-[80vh] flex flex-col">
          <div className="gradient-strip flex-none" aria-hidden="true" />

          <div className="px-6 pt-5 pb-3 flex-none flex items-center justify-between">
            <h2
              id="manage-clients-title"
              className="text-sm font-sans font-semibold text-text-primary"
            >
              Manage Clients
            </h2>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onNewClient}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-sans text-accent-saffron/80 hover:text-accent-saffron border border-surface-border rounded-md transition-colors"
              >
                <Plus size={12} aria-hidden="true" />
                New Client
              </button>
              <button
                onClick={onClose}
                aria-label="Close dialog"
                className="text-text-primary/40 hover:text-text-primary/70 transition-colors rounded focus-visible:ring-2 focus-visible:ring-accent-saffron"
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>
          </div>

          <div className="overflow-y-auto flex-1 px-6 pb-6 space-y-4">
            {active.length === 0 && inactive.length === 0 && (
              <p className="text-sm text-text-primary/40 font-sans py-4 text-center">
                No clients yet.
              </p>
            )}

            {active.length > 0 && (
              <ClientGroup
                heading="Active"
                clients={active}
                action={(c) => (
                  <button
                    type="button"
                    onClick={() => setPendingId(c.id)}
                    disabled={isPending}
                    aria-label={`Deactivate ${c.display_name}`}
                    title="Deactivate client"
                    className="text-text-primary/30 hover:text-accent-critical transition-colors disabled:opacity-40"
                  >
                    <PowerOff size={13} aria-hidden="true" />
                  </button>
                )}
              />
            )}

            {inactive.length > 0 && (
              <ClientGroup
                heading="Inactive"
                clients={inactive}
                dim
              />
            )}
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={Boolean(pendingId)}
        title="Deactivate client?"
        description={`"${target?.display_name}" will be marked inactive. Existing projects are unaffected. You cannot undo this from the UI.`}
        confirmLabel="Deactivate"
        destructive
        onConfirm={handleConfirm}
        onCancel={() => setPendingId(null)}
      />
    </>
  )
}

function ClientGroup({
  heading,
  clients,
  dim = false,
  action,
}: {
  heading: string
  clients: Client[]
  dim?: boolean
  action?: (client: Client) => React.ReactNode
}) {
  return (
    <section>
      <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider mb-2">
        {heading} ({clients.length})
      </p>
      <ul className="space-y-1">
        {clients.map((c) => (
          <li
            key={c.id}
            className={cn(
              'flex items-center justify-between rounded-md px-3 py-2 border border-surface-border',
              dim ? 'bg-surface-deep/40' : 'bg-surface-base'
            )}
          >
            <div className="min-w-0">
              <p className={cn('text-sm font-sans truncate', dim ? 'text-text-primary/40' : 'text-text-primary')}>
                {c.display_name}
              </p>
              <p className="text-xs font-mono text-text-primary/30">{c.client_code}</p>
            </div>
            {action && (
              <div className="flex-none ml-3">{action(c)}</div>
            )}
          </li>
        ))}
      </ul>
    </section>
  )
}
