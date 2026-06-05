import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function DashboardPage() {
  return (
    <AppShell>
      <PageHeader title="Dashboard" subtitle="Home" />
      <ContentArea>
        <SkeletonScreen rows={6} />
      </ContentArea>
    </AppShell>
  )
}
