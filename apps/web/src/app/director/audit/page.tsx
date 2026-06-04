import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function DirectorAuditPage() {
  return (
    <AppShell>
      <PageHeader title="Audit" subtitle="Event feed" />
      <ContentArea>
        <SkeletonScreen rows={10} />
      </ContentArea>
    </AppShell>
  )
}
