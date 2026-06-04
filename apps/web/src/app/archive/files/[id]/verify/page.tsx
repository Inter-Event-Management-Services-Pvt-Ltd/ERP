import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default async function VerifyPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return (
    <AppShell>
      <PageHeader title="Verify" subtitle={`File ${id}`} />
      <ContentArea>
        <SkeletonScreen rows={4} />
      </ContentArea>
    </AppShell>
  )
}
