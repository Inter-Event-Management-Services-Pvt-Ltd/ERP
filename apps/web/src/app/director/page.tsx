import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function DirectorDashboardPage() {
  return (
    <AppShell>
      <PageHeader title="Director Dashboard" subtitle="Overview" />
      <ContentArea>
        <SkeletonScreen rows={8} />
      </ContentArea>
    </AppShell>
  )
}
