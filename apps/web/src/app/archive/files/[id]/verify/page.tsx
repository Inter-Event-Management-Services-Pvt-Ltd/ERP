'use client'

import { use, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ChevronRight, Loader2 } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { usePhysicalFile, useVerifyPhysicalFile } from '@/hooks/use-physical-archive'
import { apiErrorMessage } from '@/lib/errors'

interface Props {
  params: Promise<{ id: string }>
}

export default function VerifyPage({ params }: Props) {
  const { id } = use(params)
  const router = useRouter()
  const { data: file, isLoading } = usePhysicalFile(id)
  const { mutate: verify, isPending } = useVerifyPhysicalFile(id)

  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    verify(
      { notes: notes.trim() || undefined },
      {
        onSuccess: () => router.push(`/archive/files/${id}`),
        onError: (err) => setError(apiErrorMessage(err)),
      }
    )
  }

  return (
    <AppShell>
      <PageHeader
        title="Verify File"
        subtitle={
          <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-text-primary/40 font-sans">
            <Link href="/archive" className="hover:text-text-primary/70 transition-colors">Archive</Link>
            <ChevronRight size={12} aria-hidden="true" />
            <Link href={`/archive/files/${id}`} className="hover:text-text-primary/70 transition-colors">
              {file?.file_code ?? id}
            </Link>
            <ChevronRight size={12} aria-hidden="true" />
            <span className="text-text-primary/60">Verify</span>
          </nav>
        }
      />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={4} />}

        {!isLoading && file && (
          <form onSubmit={handleSubmit} className="max-w-md space-y-4">
            <div className="rounded-lg border border-surface-border bg-surface-raised px-4 py-3">
              <p className="text-xs text-text-primary/40 font-sans uppercase tracking-wider mb-1">File</p>
              <p className="text-sm font-mono text-text-primary">{file.file_code}</p>
              <p className="text-xs font-mono text-text-primary/40 mt-0.5">State: {file.state}</p>
              {file.description && (
                <p className="text-xs font-sans text-text-primary/50 mt-0.5">{file.description}</p>
              )}
            </div>

            <div>
              <label htmlFor="verify-notes" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                Verification notes <span className="text-text-primary/30">(optional)</span>
              </label>
              <textarea
                id="verify-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Physical condition observed, verifier name, etc."
                className="w-full rounded-md border border-surface-border bg-surface-base px-3 py-2 text-sm font-sans text-text-primary placeholder:text-text-primary/30 focus:outline-none focus:ring-2 focus:ring-accent-saffron resize-none"
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
                Record Verification
              </button>
            </div>
          </form>
        )}
      </ContentArea>
    </AppShell>
  )
}
