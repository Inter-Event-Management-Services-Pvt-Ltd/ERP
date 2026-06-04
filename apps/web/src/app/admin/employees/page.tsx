import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function AdminEmployeesPage() {
  return (
    <AppShell>
      <PageHeader title="Employees" subtitle="Management" />
      <ContentArea>
        <SkeletonScreen rows={8} />
      </ContentArea>
    </AppShell>
  )
}
