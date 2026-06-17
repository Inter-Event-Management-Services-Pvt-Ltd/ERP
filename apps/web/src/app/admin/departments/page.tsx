'use client'

import { Building2 } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { useDepartments } from '@/hooks/use-employees'
import type { Department } from '@/types'

export default function AdminDepartmentsPage() {
  const { data: departments, isLoading, error, refetch } = useDepartments()

  return (
    <AppShell>
      <PageHeader title="Departments" subtitle="Organisation unit reference" />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={5} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && departments?.length === 0 && (
          <EmptyState icon={Building2} heading="No departments" body="No departments have been created yet." />
        )}

        {!isLoading && !error && departments && departments.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Code', 'Name'].map((h) => (
                    <th key={h} scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {departments.map((dept: Department, i: number) => (
                  <tr
                    key={dept.id}
                    className={`border-b border-surface-border last:border-0 ${i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'}`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">{dept.code}</td>
                    <td className="px-4 py-3 text-text-primary/80">{dept.name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
