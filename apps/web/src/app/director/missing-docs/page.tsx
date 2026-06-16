'use client'

import { FileX } from 'lucide-react'
import Link from 'next/link'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { useDirectorMissingDocuments } from '@/hooks/use-director'

export default function DirectorMissingDocsPage() {
  const { data: items, isLoading, error, refetch } = useDirectorMissingDocuments({ limit: 100 })

  return (
    <AppShell>
      <PageHeader
        title="Missing Required Documents"
        subtitle="Active projects with unfulfilled required document types"
      />
      <ContentArea>
        {isLoading && <SkeletonScreen rows={8} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && items?.length === 0 && (
          <EmptyState
            icon={FileX}
            heading="All required documents present"
            body="No active projects are missing required documents."
          />
        )}

        {!isLoading && !error && items && items.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Project', 'Missing Document Type'].map((h) => (
                    <th
                      key={h}
                      scope="col"
                      className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((item, i) => (
                  <tr
                    key={`${item.project_id}-${item.document_type_id}`}
                    className={`border-b border-surface-border last:border-0 ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Link
                        href={`/projects/${item.project_id}`}
                        className="hover:text-accent-saffron transition-colors"
                      >
                        <span className="font-mono text-xs text-text-primary/40 mr-1.5">{item.project_code}</span>
                        <span className="text-text-primary/80 font-medium">{item.project_name}</span>
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs text-accent-critical/80 mr-1.5">{item.document_type_code}</span>
                      <span className="text-text-primary/70">{item.document_type_name}</span>
                    </td>
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
