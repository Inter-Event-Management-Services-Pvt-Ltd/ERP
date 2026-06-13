'use client'

import { use, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ScanLine } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { EmptyState } from '@/components/states/empty-state'
import { usePhysicalFileByQrToken } from '@/hooks/use-physical-archive'
import { apiErrorMessage } from '@/lib/errors'

interface Props {
  params: Promise<{ qr_token: string }>
}

export default function ArchiveScanPage({ params }: Props) {
  const { qr_token: qrToken } = use(params)
  const router = useRouter()
  const { data: file, isLoading, error } = usePhysicalFileByQrToken(qrToken)

  useEffect(() => {
    if (file) router.replace(`/archive/files/${file.id}`)
  }, [file, router])

  const notFound = (error as { code?: string } | null)?.code === 'NOT_FOUND'

  return (
    <AppShell>
      <PageHeader title="Scan Result" />
      <ContentArea>
        {(isLoading || file) && <SkeletonScreen rows={4} />}

        {!isLoading && !file && error && notFound && (
          <EmptyState
            icon={ScanLine}
            heading="Label not found"
            body="This QR code does not match any physical archive file. It may have been removed, deactivated, or the code may be invalid."
            action={
              <Link
                href="/archive"
                className="text-sm font-sans text-accent-saffron hover:text-accent-saffron/80 transition-colors"
              >
                ← Back to Archive
              </Link>
            }
          />
        )}

        {!isLoading && !file && error && !notFound && (
          <ErrorState message={apiErrorMessage(error)} />
        )}
      </ContentArea>
    </AppShell>
  )
}
