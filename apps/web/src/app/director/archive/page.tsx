import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function DirectorArchivePage() {
  return (
    <AppShell>
      <PageHeader title="Archive" subtitle="Storage view" />
      <ContentArea>
        <SkeletonScreen rows={5} />
      </ContentArea>
    </AppShell>
  )
}
