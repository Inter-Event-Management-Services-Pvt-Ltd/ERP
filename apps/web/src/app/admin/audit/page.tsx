'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { ChevronDown, ChevronRight, Activity } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { useAuditEvents } from '@/hooks/use-admin'
import { useMe } from '@/hooks/use-me'
import type { AuditEvent } from '@/types'

const inputCls = 'px-3 py-2 text-sm bg-surface-base border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50'
const labelCls = 'text-xs font-semibold text-text-primary/60 uppercase tracking-wide'

const PAGE_LIMIT = 50

function JsonBlock({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="text-[10px] font-mono text-text-primary/60 bg-surface-deep rounded p-2 overflow-x-auto max-h-40 whitespace-pre-wrap break-all">
      {JSON.stringify(data, null, 2)}
    </pre>
  )
}

function AuditRow({ event }: { event: AuditEvent }) {
  const [expanded, setExpanded] = useState(false)
  const hasDetail =
    (event.old_values && Object.keys(event.old_values).length > 0) ||
    (event.new_values && Object.keys(event.new_values).length > 0) ||
    (event.metadata && Object.keys(event.metadata).length > 0)

  return (
    <>
      <tr className="border-b border-surface-border last:border-0 hover:bg-surface-raised/40 transition-colors">
        <td className="px-4 py-3 whitespace-nowrap">
          <div className="flex items-center gap-1.5">
            {hasDetail && (
              <button
                type="button"
                aria-label={expanded ? 'Collapse' : 'Expand'}
                onClick={() => setExpanded((x) => !x)}
                className="text-text-primary/30 hover:text-accent-saffron transition-colors"
              >
                {expanded ? <ChevronDown size={12} aria-hidden="true" /> : <ChevronRight size={12} aria-hidden="true" />}
              </button>
            )}
            <span className="text-xs font-mono text-text-primary/40 mr-1">{event.actor.employee_code}</span>
            <span className="text-xs text-text-primary/80">{event.actor.full_name}</span>
          </div>
        </td>
        <td className="px-4 py-3 whitespace-nowrap">
          <span className="font-mono text-xs text-accent-saffron/80">{event.action_code}</span>
        </td>
        <td className="px-4 py-3 text-xs text-text-primary/50 font-mono whitespace-nowrap">{event.resource_type}</td>
        <td className="px-4 py-3 text-xs text-text-primary/40 font-mono whitespace-nowrap">{event.resource_id.slice(0, 8)}…</td>
        <td className="px-4 py-3 text-xs text-text-primary/40 font-mono whitespace-nowrap">
          {format(new Date(event.created_at), 'dd MMM HH:mm:ss')}
        </td>
      </tr>
      {expanded && hasDetail && (
        <tr className="border-b border-surface-border bg-surface-deep/50">
          <td colSpan={5} className="px-6 py-3">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {event.old_values && Object.keys(event.old_values).length > 0 && (
                <div>
                  <p className={`${labelCls} mb-1.5`}>Before</p>
                  <JsonBlock data={event.old_values} />
                </div>
              )}
              {event.new_values && Object.keys(event.new_values).length > 0 && (
                <div>
                  <p className={`${labelCls} mb-1.5`}>After</p>
                  <JsonBlock data={event.new_values} />
                </div>
              )}
              {event.metadata && Object.keys(event.metadata).length > 0 && (
                <div>
                  <p className={`${labelCls} mb-1.5`}>Metadata</p>
                  <JsonBlock data={event.metadata} />
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function AdminAuditPage() {
  const { data: user } = useMe()
  const canView = (user?.isSuperUser ?? false) || (user?.permissions.includes('audit.view') ?? false)

  const [actionCode, setActionCode] = useState('')
  const [resourceType, setResourceType] = useState('')
  const [resourceId, setResourceId] = useState('')
  const [actorId, setActorId] = useState('')
  const [createdFrom, setCreatedFrom] = useState('')
  const [createdTo, setCreatedTo] = useState('')
  const [offset, setOffset] = useState(0)

  const params = {
    action_code: actionCode.trim() || undefined,
    resource_type: resourceType.trim() || undefined,
    resource_id: resourceId.trim() || undefined,
    actor_employee_id: actorId.trim() || undefined,
    created_from: createdFrom || undefined,
    created_to: createdTo || undefined,
    limit: PAGE_LIMIT,
    offset,
  }

  const { data: events, isLoading, error, refetch } = useAuditEvents(canView ? params : undefined)

  function handleFilter(e: React.FormEvent) {
    e.preventDefault()
    setOffset(0)
    refetch()
  }

  function clearFilters() {
    setActionCode('')
    setResourceType('')
    setResourceId('')
    setActorId('')
    setCreatedFrom('')
    setCreatedTo('')
    setOffset(0)
  }

  if (!canView) {
    return (
      <AppShell>
        <PageHeader title="Audit Log" subtitle="Full system history" />
        <ContentArea>
          <p className="text-sm text-text-primary/40">You do not have permission to view audit events.</p>
        </ContentArea>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <PageHeader title="Audit Log" subtitle="Full system history" />

      <ContentArea>
        {/* Filters */}
        <form onSubmit={handleFilter} className="mb-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 p-4 bg-surface-base border border-surface-border rounded-lg">
          <div className="flex flex-col gap-1.5">
            <label className={labelCls}>Action Code</label>
            <input className={inputCls} value={actionCode} onChange={(e) => setActionCode(e.target.value)} placeholder="document.upload" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className={labelCls}>Resource Type</label>
            <input className={inputCls} value={resourceType} onChange={(e) => setResourceType(e.target.value)} placeholder="physical_file" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className={labelCls}>Resource ID</label>
            <input className={inputCls} value={resourceId} onChange={(e) => setResourceId(e.target.value)} placeholder="UUID" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className={labelCls}>Actor Employee ID</label>
            <input className={inputCls} value={actorId} onChange={(e) => setActorId(e.target.value)} placeholder="UUID" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className={labelCls}>From</label>
            <input type="date" className={inputCls} value={createdFrom} onChange={(e) => setCreatedFrom(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className={labelCls}>To</label>
            <input type="date" className={inputCls} value={createdTo} onChange={(e) => setCreatedTo(e.target.value)} />
          </div>
          <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-3">
            <button type="submit" className="px-3 py-2 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors">
              Apply
            </button>
            <button type="button" onClick={clearFilters} className="px-3 py-2 text-xs text-text-primary/50 hover:text-text-primary transition-colors">
              Clear
            </button>
          </div>
        </form>

        {isLoading && <SkeletonScreen rows={10} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && events?.length === 0 && (
          <EmptyState icon={Activity} heading="No audit events" body="No events match the current filters." />
        )}

        {!isLoading && !error && events && events.length > 0 && (
          <>
            <div className="overflow-x-auto rounded-lg border border-surface-border">
              <table className="w-full text-sm font-sans">
                <thead>
                  <tr className="border-b border-surface-border bg-surface-raised">
                    {['Actor', 'Action', 'Resource Type', 'Resource', 'Time'].map((h) => (
                      <th key={h} scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {events.map((ev: AuditEvent) => (
                    <AuditRow key={ev.id} event={ev} />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-4">
              <span className="text-xs text-text-primary/40 font-mono">
                Showing {offset + 1}–{offset + events.length}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setOffset(Math.max(0, offset - PAGE_LIMIT))}
                  disabled={offset === 0}
                  className="px-3 py-1.5 text-xs text-text-primary/60 border border-surface-border rounded-lg hover:text-text-primary transition-colors disabled:opacity-30"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setOffset(offset + PAGE_LIMIT)}
                  disabled={events.length < PAGE_LIMIT}
                  className="px-3 py-1.5 text-xs text-text-primary/60 border border-surface-border rounded-lg hover:text-text-primary transition-colors disabled:opacity-30"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </ContentArea>
    </AppShell>
  )
}
