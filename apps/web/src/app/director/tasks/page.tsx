import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function DirectorTasksPage() {
  return (
    <AppShell>
      <PageHeader title="Tasks" subtitle="Workload" />
      <ContentArea>
        <SkeletonScreen rows={7} />
      </ContentArea>
    </AppShell>
  )
}
