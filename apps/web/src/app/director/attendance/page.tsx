import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'

export default function DirectorAttendancePage() {
  return (
    <AppShell>
      <PageHeader title="Attendance" subtitle="Company-wide" />
      <ContentArea>
        <SkeletonScreen rows={6} />
      </ContentArea>
    </AppShell>
  )
}
