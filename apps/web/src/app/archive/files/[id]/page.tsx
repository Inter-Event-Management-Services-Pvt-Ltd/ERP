'use client'

import { use } from 'react'
import Link from 'next/link'
import { ChevronRight, LogIn, LogOut, ArrowRightLeft, ShieldCheck, Tag, Printer } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { usePhysicalFile, usePhysicalFileLabel } from '@/hooks/use-physical-archive'
import { useMe } from '@/hooks/use-me'
import { cn } from '@/lib/utils'
import { format } from 'date-fns'
import { locationDisplayName } from '@/lib/locations'
import type { PhysicalFileState } from '@/types'

const STATE_LABEL: Record<PhysicalFileState, string> = {
  AVAILABLE: 'Available',
  CHECKED_OUT: 'Checked Out',
  MISSING: 'Missing',
  UNDER_VERIFICATION: 'Under Verification',
  ARCHIVED: 'Archived',
}

const STATE_CLASS: Record<PhysicalFileState, string> = {
  AVAILABLE: 'text-green-400',
  CHECKED_OUT: 'text-accent-warning',
  MISSING: 'text-accent-critical',
  UNDER_VERIFICATION: 'text-accent-saffron',
  ARCHIVED: 'text-text-primary/30',
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
        title={file?.physical_file_code ?? 'Physical File'}
        subtitle={
          <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-text-primary/40 font-sans">
            <Link href="/archive" className="hover:text-text-primary/70 transition-colors">
              Archive
            </Link>
            <ChevronRight size={12} aria-hidden="true" />
            <span className="text-text-primary/60">{file?.physical_file_code ?? id}</span>
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <InfoCard label="File Code" value={file.physical_file_code} mono />
              <InfoCard
                label="Status"
                value={STATE_LABEL[file.status]}
                valueClass={STATE_CLASS[file.status]}
              />
              {file.archive_location ? (
                <InfoCard
                  label="Location"
                  value={locationDisplayName(file.archive_location)}
                  sub={file.archive_room ? `${file.archive_room.name} · ${file.archive_location.location_type}` : file.archive_location.location_type}
                />
              ) : (
                <InfoCard label="Location" value="—" />
              )}
              {file.project ? (
                <InfoCard
                  label="Project"
                  value={file.project.name}
                  sub={file.project.project_code}
                />
              ) : (
                <InfoCard label="Project" value="—" />
              )}
            </div>

            {file.notes && (
              <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3">
                <p className="text-xs text-text-primary/40 font-sans uppercase tracking-wider mb-1">Notes</p>
                <p className="text-sm font-sans text-text-primary/80">{file.notes}</p>
              </div>
            )}

            {file.status === 'CHECKED_OUT' && file.open_checkout && (
              <div className="rounded-lg border border-accent-warning/20 bg-accent-warning/5 px-4 py-3 space-y-1">
                <p className="text-xs font-sans text-accent-warning font-semibold">Currently checked out</p>
                <p className="text-xs font-mono text-text-primary/50">
                  Since {format(new Date(file.open_checkout.checked_out_at), 'dd MMM yyyy HH:mm')}
                </p>
                <p className="text-xs font-sans text-text-primary/50">{file.open_checkout.purpose}</p>
                {file.open_checkout.expected_return_at && (
                  <p className="text-xs font-mono text-text-primary/40">
                    Expected back {format(new Date(file.open_checkout.expected_return_at), 'dd MMM yyyy')}
                  </p>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-4 space-y-3">
              <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
                Actions
              </p>
              <div className="flex flex-wrap gap-2">
                {canCheckout && file.status === 'AVAILABLE' && (
                  <ActionLink
                    href={`/archive/files/${id}/checkout`}
                    icon={<LogIn size={13} />}
                    label="Check Out"
                  />
                )}
                {canManage && file.status === 'CHECKED_OUT' && (
                  <ActionLink
                    href={`/archive/files/${id}/return`}
                    icon={<LogOut size={13} />}
                    label="Return"
                  />
                )}
                {canManage && (file.status === 'AVAILABLE' || file.status === 'CHECKED_OUT') && (
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
              <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-4 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Tag size={14} className="text-accent-saffron" aria-hidden="true" />
                    <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
                      QR Label
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => window.print()}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-sans text-text-primary/60 border border-surface-border rounded-md hover:bg-surface-raised hover:text-text-primary transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron"
                  >
                    <Printer size={13} aria-hidden="true" />
                    Print Label
                  </button>
                </div>
                <div className="inline-flex flex-col items-center gap-2 rounded-lg bg-white px-5 py-4">
                  <QRCodeSVG
                    value={label.qr_token}
                    size={128}
                    bgColor="#ffffff"
                    fgColor="#000000"
                    level="M"
                  />
                  <p className="text-sm font-mono text-black font-semibold">{label.physical_file_code}</p>
                  <div className="text-center">
                    <p className="text-[10px] font-sans uppercase tracking-wider text-gray-400">Archive Location</p>
                    <p className="text-xs font-mono text-gray-600">
                      {label.archive_room} · {label.location_code}
                    </p>
                  </div>
                  <p className="text-xs font-sans text-gray-500 text-center">{label.project_name}</p>
                </div>
                <div className="flex items-center gap-3">
                  <p className="text-xs font-mono text-text-primary/25 break-all flex-1">{label.qr_token}</p>
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(label.qr_token)}
                    className="flex-none text-xs text-accent-saffron/60 hover:text-accent-saffron transition-colors font-sans"
                  >
                    Copy
                  </button>
                </div>
              </div>
            )}

            {/* Print-only label layout — shown solely when printing (see globals.css "print-label" rules) */}
            {label && (
              <div className="print-label hidden print:flex flex-col items-center gap-3 text-center">
                <QRCodeSVG
                  value={label.qr_token}
                  size={180}
                  bgColor="#ffffff"
                  fgColor="#000000"
                  level="M"
                />
                <p className="text-lg font-mono font-bold text-black">{label.physical_file_code}</p>
                <p className="text-sm font-sans text-black">{label.project_name}</p>
                <div>
                  <p className="text-[10px] font-sans uppercase tracking-wider text-black/50">Archive Location</p>
                  <p className="text-sm font-mono text-black">
                    {label.archive_room} · {label.location_code}
                  </p>
                </div>
                <p className="text-xs font-sans text-black max-w-xs">{label.label_text}</p>
              </div>
            )}

            <dl className="flex flex-wrap gap-x-6 gap-y-1 text-xs font-mono text-text-primary/30">
              <div className="flex gap-1"><dt>ID:</dt><dd>{file.id}</dd></div>
              <div className="flex gap-1"><dt>Volume:</dt><dd>{file.volume_number}</dd></div>
              {file.archived_on && (
                <div className="flex gap-1">
                  <dt>Archived on:</dt>
                  <dd>{format(new Date(file.archived_on), 'dd MMM yyyy')}</dd>
                </div>
              )}
              {file.last_verified_at && (
                <div className="flex gap-1">
                  <dt>Last verified:</dt>
                  <dd>{format(new Date(file.last_verified_at), 'dd MMM yyyy')}</dd>
                </div>
              )}
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
