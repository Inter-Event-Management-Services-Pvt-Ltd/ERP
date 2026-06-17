'use client'

import { ShieldCheck } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { useRoles } from '@/hooks/use-employees'
import type { RoleDetail } from '@/types'

export default function AdminRolesPage() {
  const { data: roles, isLoading, error, refetch } = useRoles()

  return (
    <AppShell>
      <PageHeader title="Roles" subtitle="System role reference" />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={6} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && roles?.length === 0 && (
          <EmptyState icon={ShieldCheck} heading="No roles" body="No roles have been defined yet." />
        )}

        {!isLoading && !error && roles && roles.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Code', 'Name', 'Description'].map((h) => (
                    <th key={h} scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {roles.map((role: RoleDetail, i: number) => (
                  <tr
                    key={role.id}
                    className={`border-b border-surface-border last:border-0 ${i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'}`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">{role.code}</td>
                    <td className="px-4 py-3 font-medium text-text-primary/80 whitespace-nowrap">{role.name}</td>
                    <td className="px-4 py-3 text-xs text-text-primary/50">{role.description ?? '—'}</td>
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
