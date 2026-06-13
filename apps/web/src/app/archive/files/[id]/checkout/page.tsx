'use client'

import { use, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ChevronRight, Loader2 } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { usePhysicalFile, useCheckoutPhysicalFile } from '@/hooks/use-physical-archive'
import { apiErrorMessage } from '@/lib/errors'

interface Props {
  params: Promise<{ id: string }>
}

export default function CheckoutPage({ params }: Props) {
  const { id } = use(params)
  const router = useRouter()
  const { data: file, isLoading } = usePhysicalFile(id)
  const { mutate: checkout, isPending } = useCheckoutPhysicalFile(id)

  const [purpose, setPurpose] = useState('')
  const [expectedReturnAt, setExpectedReturnAt] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!purpose.trim()) { setError('Purpose is required.'); return }
    if (!expectedReturnAt) { setError('Expected return date is required.'); return }
    setError(null)
    checkout(
      {
        purpose: purpose.trim(),
        expected_return_at: expectedReturnAt,
      },
      {
        onSuccess: () => router.push(`/archive/files/${id}`),
        onError: (err) => setError(apiErrorMessage(err)),
      }
    )
  }

  return (
    <AppShell>
      <PageHeader
        title="Check Out File"
        subtitle={
          <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-text-primary/40 font-sans">
            <Link href="/archive" className="hover:text-text-primary/70 transition-colors">Archive</Link>
            <ChevronRight size={12} aria-hidden="true" />
            <Link href={`/archive/files/${id}`} className="hover:text-text-primary/70 transition-colors">
              {file?.physical_file_code ?? id}
            </Link>
            <ChevronRight size={12} aria-hidden="true" />
            <span className="text-text-primary/60">Check Out</span>
          </nav>
        }
      />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={4} />}

        {!isLoading && file && file.status !== 'AVAILABLE' && (
          <div className="rounded-lg border border-accent-warning/30 bg-accent-warning/5 px-4 py-3 max-w-md">
            <p className="text-sm font-sans text-accent-warning">
              This file is currently <strong>{file.status}</strong> and cannot be checked out.
            </p>
            <Link href={`/archive/files/${id}`} className="text-xs text-accent-saffron/70 hover:text-accent-saffron mt-2 block">
              ← Back to file
            </Link>
          </div>
        )}

        {!isLoading && file && file.status === 'AVAILABLE' && (
          <form onSubmit={handleSubmit} className="max-w-md space-y-4">
            <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3">
              <p className="text-xs text-text-primary/40 font-sans uppercase tracking-wider mb-1">File</p>
              <p className="text-sm font-mono text-text-primary">{file.physical_file_code}</p>
              {file.notes && (
                <p className="text-xs font-sans text-text-primary/50 mt-0.5">{file.notes}</p>
              )}
            </div>

            <div>
              <label htmlFor="checkout-purpose" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                Purpose <span className="text-accent-critical">*</span>
              </label>
              <textarea
                id="checkout-purpose"
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                rows={3}
                placeholder="Reason for checkout, destination, etc."
                className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary placeholder:text-text-primary/30 focus:outline-none focus:ring-2 focus:ring-accent-saffron resize-none"
              />
            </div>

            <div>
              <label htmlFor="checkout-expected-return" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                Expected return date <span className="text-accent-critical">*</span>
              </label>
              <input
                id="checkout-expected-return"
                type="date"
                required
                aria-required="true"
                value={expectedReturnAt}
                onChange={(e) => setExpectedReturnAt(e.target.value)}
                className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-saffron"
              />
            </div>

            {error && <p role="alert" className="text-xs font-sans text-accent-critical">{error}</p>}

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => router.push(`/archive/files/${id}`)}
                className="px-4 py-2 text-sm font-sans rounded-md border border-surface-border text-text-primary/70 hover:text-text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isPending}
                className="flex items-center gap-1.5 px-4 py-2 text-sm font-sans font-medium rounded-md bg-accent-saffron text-surface-deep hover:bg-accent-warning disabled:opacity-40 transition-colors"
              >
                {isPending && <Loader2 size={14} className="animate-spin" aria-hidden="true" />}
                Confirm Check Out
              </button>
            </div>
          </form>
        )}
      </ContentArea>
    </AppShell>
  )
}
