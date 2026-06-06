'use client'

import { use } from 'react'
import Link from 'next/link'
import { ChevronRight, LogIn, LogOut, ArrowRightLeft, ShieldCheck, Tag } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { usePhysicalFile, usePhysicalFileLabel } from '@/hooks/use-physical-archive'
import { useMe } from '@/hooks/use-me'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'
import type { PhysicalFileState } from '@/types'

const STATE_LABEL: Record<PhysicalFileState, string> = {
  IN_STORAGE: 'In Storage',
  CHECKED_OUT: 'Checked Out',
  MISSING: 'Missing',
  DISPOSED: 'Disposed',
}

const STATE_CLASS: Record<PhysicalFileState, string> = {
  IN_STORAGE: 'text-green-400',
  CHECKED_OUT: 'text-accent-warning',
  MISSING: 'text-accent-critical',
  DISPOSED: 'text-text-primary/30',
}

interface Props {
  params: Promise<{ id: string }>
}

export default function PhysicalFileDetailPage({ params }: Props) {
  const { id } = use(params)
  const { data: user } = useMe()
  const { data: file, isLoading, error, refetch } = usePhysicalFile(id)
  const { data: label } = usePhysicalFileLabel(id)

  const canCheckout = user?.isSuperUser || user?.permissions.includes('physical_file.checkout')
  const canManage = user?.isSuperUser || user?.permissions.includes('archive.manage')

  return (
    <AppShell>
      <PageHeader
        title={file?.file_code ?? 'Physical File'}
        subtitle={
          <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-text-primary/40 font-sans">
            <Link href="/archive" className="hover:text-text-primary/70 transition-colors">
              Archive
            </Link>
            <ChevronRight size={12} aria-hidden="true" />
            <span className="text-text-primary/60">{file?.file_code ?? id}</span>
          </nav>
        }
      />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={6} />}

        {!isLoading && error && (
          <ErrorState
            message="Failed to load physical file."
            onRetry={() => refetch()}
          />
        )}

        {!isLoading && !error && file && (
          <div className="space-y-5">
            {/* State + details */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <InfoCard label="File Code" value={file.file_code} mono />
              <InfoCard
                label="State"
                value={STATE_LABEL[file.state]}
                valueClass={STATE_CLASS[file.state]}
              />
              {file.location && (
                <InfoCard
                  label="Location"
                  value={file.location.label}
                  sub={file.location.type}
                />
              )}
              {!file.location && (
                <InfoCard label="Location" value="—" />
              )}
            </div>

            {file.description && (
              <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3">
                <p className="text-xs text-text-primary/40 font-sans uppercase tracking-wider mb-1">Description</p>
                <p className="text-sm font-sans text-text-primary/80">{file.description}</p>
              </div>
            )}

            {file.state === 'CHECKED_OUT' && file.checked_out_at && (
              <div className="rounded-lg border border-accent-warning/20 bg-accent-warning/5 px-4 py-3">
                <p className="text-xs font-sans text-accent-warning font-semibold mb-1">Currently checked out</p>
                <p className="text-xs font-mono text-text-primary/50">
                  Since {format(new Date(file.checked_out_at), 'dd MMM yyyy HH:mm')}
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-4 space-y-3">
              <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
                Actions
              </p>
              <div className="flex flex-wrap gap-2">
                {canCheckout && file.state === 'IN_STORAGE' && (
                  <ActionLink
                    href={`/archive/files/${id}/checkout`}
                    icon={<LogIn size={13} />}
                    label="Check Out"
                  />
                )}
                {canManage && file.state === 'CHECKED_OUT' && (
                  <ActionLink
                    href={`/archive/files/${id}/return`}
                    icon={<LogOut size={13} />}
                    label="Return"
                  />
                )}
                {canManage && (file.state === 'IN_STORAGE' || file.state === 'CHECKED_OUT') && (
                  <ActionLink
                    href={`/archive/files/${id}/move`}
                    icon={<ArrowRightLeft size={13} />}
                    label="Move"
                  />
                )}
                {canManage && (
                  <ActionLink
                    href={`/archive/files/${id}/verify`}
                    icon={<ShieldCheck size={13} />}
                    label="Verify"
                  />
                )}
                {!canCheckout && !canManage && (
                  <p className="text-xs font-sans text-text-primary/40">No actions available for your role.</p>
                )}
              </div>
            </div>

            {/* QR Label */}
            {label && (
              <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-4 space-y-2">
                <div className="flex items-center gap-2">
                  <Tag size={14} className="text-accent-saffron" aria-hidden="true" />
                  <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
                    QR Label
                  </p>
                </div>
                <div className="rounded-md bg-surface-base border border-surface-border/50 px-4 py-3 space-y-1.5">
                  <p className="text-sm font-mono text-text-primary">{label.file_code}</p>
                  {label.location_label && (
                    <p className="text-xs font-mono text-text-primary/50">{label.location_label}</p>
                  )}
                  {label.project_name && (
                    <p className="text-xs font-sans text-text-primary/50">{label.project_name}</p>
                  )}
                  <div className="pt-1 border-t border-surface-border/50">
                    <p className="text-xs font-sans text-text-primary/30 mb-1">QR token (OPEN-028: QR rendering pending library approval)</p>
                    <p className="text-xs font-mono text-text-primary/60 break-all">{label.qr_token}</p>
                    <button
                      type="button"
                      onClick={() => navigator.clipboard.writeText(label.qr_token)}
                      className="mt-1 text-xs text-accent-saffron/60 hover:text-accent-saffron transition-colors font-sans"
                    >
                      Copy token
                    </button>
                  </div>
                </div>
              </div>
            )}

            <dl className="flex flex-wrap gap-x-6 gap-y-1 text-xs font-mono text-text-primary/30">
              <div className="flex gap-1"><dt>ID:</dt><dd>{file.id}</dd></div>
              <div className="flex gap-1"><dt>Project:</dt><dd>{file.project_id}</dd></div>
              <div className="flex gap-1">
                <dt>Registered:</dt>
                <dd>{format(new Date(file.created_at), 'dd MMM yyyy')}</dd>
              </div>
            </dl>
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}

function InfoCard({
  label,
  value,
  sub,
  mono = false,
  valueClass,
}: {
  label: string
  value: string
  sub?: string
  mono?: boolean
  valueClass?: string
}) {
  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3 space-y-1">
      <p className="text-xs text-text-primary/40 font-sans uppercase tracking-wider">{label}</p>
      <p className={cn('text-sm font-medium leading-snug', mono ? 'font-mono' : 'font-sans', valueClass ?? 'text-text-primary')}>
        {value}
      </p>
      {sub && <p className="text-xs font-mono text-text-primary/30">{sub}</p>}
    </div>
  )
}

function ActionLink({
  href,
  icon,
  label,
}: {
  href: string
  icon: React.ReactNode
  label: string
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans text-text-primary/60 border border-surface-border rounded-md hover:bg-surface-raised hover:text-text-primary transition-colors"
    >
      {icon}
      {label}
    </Link>
  )
}
