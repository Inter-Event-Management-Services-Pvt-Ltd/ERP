import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function ArchivePage() {
  return (
    <AppShell>
      <PageHeader title="Archive" subtitle="Overview" />
      <ContentArea>
        <SkeletonScreen rows={5} />
      </ContentArea>
    </AppShell>
  )
}
