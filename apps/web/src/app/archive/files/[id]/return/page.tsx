import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default async function ReturnPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return (
    <AppShell>
      <PageHeader title="Return" subtitle={`File ${id}`} />
      <ContentArea>
        <SkeletonScreen rows={4} />
      </ContentArea>
    </AppShell>
  )
}
