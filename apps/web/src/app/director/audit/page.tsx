'use client'

import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Activity } from 'lucide-react'
import { useDirectorAuditEvents } from '@/hooks/use-director'

function FilterInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] font-mono uppercase tracking-widest text-text-primary/40">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="h-8 px-3 text-xs font-mono bg-surface-raised border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50 w-48"
      />
    </div>
  )
}

export default function DirectorAuditPage() {
  const [actionCode, setActionCode] = useState('')
  const [resourceType, setResourceType] = useState('')
  const [debouncedActionCode, setDebouncedActionCode] = useState('')
  const [debouncedResourceType, setDebouncedResourceType] = useState('')

  useEffect(() => {
    const t = setTimeout(() => setDebouncedActionCode(actionCode.trim()), 300)
    return () => clearTimeout(t)
  }, [actionCode])

  useEffect(() => {
    const t = setTimeout(() => setDebouncedResourceType(resourceType.trim()), 300)
    return () => clearTimeout(t)
  }, [resourceType])

  const params = {
    action_code: debouncedActionCode || undefined,
    resource_type: debouncedResourceType || undefined,
    limit: 100,
  }

  const { data: events, isLoading, error, refetch } = useDirectorAuditEvents(params)

  return (
    <AppShell>
      <PageHeader title="Audit Events" subtitle="System activity log" />

      <ContentArea>
        <div className="flex flex-wrap gap-4 mb-5">
          <FilterInput
            label="Action code"
            value={actionCode}
            onChange={setActionCode}
            placeholder="e.g. document.downloaded"
          />
          <FilterInput
            label="Resource type"
            value={resourceType}
            onChange={setResourceType}
            placeholder="e.g. document_version"
          />
        </div>

        {isLoading && <SkeletonScreen rows={10} />}

        {!isLoading && error && (
          <ErrorState
            message={
              (error as { code?: string }).code === 'PERMISSION_DENIED'
                ? 'Director access required.'
                : (error as Error).message
            }
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && events?.length === 0 && (
          <EmptyState
            icon={Activity}
            heading="No audit events"
            body={
              actionCode || resourceType
                ? 'No events match the current filters.'
                : 'No audit events recorded yet.'
            }
          />
        )}

        {!isLoading && !error && events && events.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Time', 'Actor', 'Action', 'Resource type', 'Resource ID'].map((h) => (
                    <th
                      key={h}
                      scope="col"
                      className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {events.map((ev, i) => (
                  <tr
                    key={ev.id}
                    className={`border-b border-surface-border last:border-0 ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">
                      {format(new Date(ev.created_at), 'dd MMM yyyy HH:mm:ss')}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono text-xs text-text-primary/40 mr-1.5">{ev.actor.employee_code}</span>
                      <span className="text-text-primary/80">{ev.actor.full_name}</span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-mono text-xs text-accent-saffron/80">{ev.action_code}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">
                      {ev.resource_type}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/30 whitespace-nowrap max-w-[180px] truncate">
                      {ev.resource_id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
