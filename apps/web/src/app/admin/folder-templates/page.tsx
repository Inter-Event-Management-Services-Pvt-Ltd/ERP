'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Plus, FolderOpen } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { useFolderTemplates, useCreateFolderTemplate } from '@/hooks/use-admin'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import type { FolderTemplate, CreateFolderTemplatePayload } from '@/types'

const inputCls = 'px-3 py-2 text-sm bg-surface-base border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50'
const labelCls = 'text-xs font-semibold text-text-primary/60 uppercase tracking-wide'

export default function AdminFolderTemplatesPage() {
  const { data: user } = useMe()
  const { data: templates, isLoading, error, refetch } = useFolderTemplates()
  const createMutation = useCreateFolderTemplate()

  const canManage = (user?.isSuperUser ?? false) || (user?.permissions.includes('template.manage') ?? false)

  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState<CreateFolderTemplatePayload>({ name: '', project_type_id: null })
  const [createError, setCreateError] = useState('')

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreateError('')
    if (!form.name.trim()) { setCreateError('Template name is required.'); return }
    try {
      await createMutation.mutateAsync({ ...form, project_type_id: form.project_type_id || null })
      setShowCreate(false)
      setForm({ name: '', project_type_id: null })
    } catch (err) {
      setCreateError(apiErrorMessage(err))
    }
  }

  return (
    <AppShell>
      <PageHeader
        title="Folder Templates"
        subtitle="Reusable folder structures for new projects"
        actions={
          canManage ? (
            <button
              type="button"
              onClick={() => { setShowCreate(true); setCreateError('') }}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors"
            >
              <Plus size={16} aria-hidden="true" />
              New Template
            </button>
          ) : undefined
        }
      />

      <ContentArea>
        {showCreate && (
          <div className="mb-5">
            <h2 className="text-xs font-semibold text-text-primary/40 uppercase tracking-widest mb-3">New Template</h2>
            <form onSubmit={handleCreate} className="flex flex-col gap-3 p-4 bg-surface-base border border-surface-border rounded-lg max-w-lg">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="ft-name" className={labelCls}>Name <span className="text-accent-critical">*</span></label>
                <input
                  id="ft-name"
                  className={inputCls}
                  value={form.name}
                  onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="Default Project Structure"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="ft-project-type" className={labelCls}>Project Type ID <span className="font-normal normal-case text-text-primary/30">(optional)</span></label>
                <input
                  id="ft-project-type"
                  className={inputCls}
                  value={form.project_type_id ?? ''}
                  onChange={(e) => setForm(f => ({ ...f, project_type_id: e.target.value || null }))}
                  placeholder="UUID of a project type"
                />
              </div>
              {createError && <p role="alert" className="text-xs text-accent-critical">{createError}</p>}
              <div className="flex gap-3 pt-1">
                <button type="submit" disabled={createMutation.isPending} className="px-3 py-1.5 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
                  {createMutation.isPending ? 'Creating…' : 'Create Template'}
                </button>
                <button type="button" onClick={() => { setShowCreate(false); setCreateError('') }} className="px-3 py-1.5 text-xs text-text-primary/60 hover:text-text-primary transition-colors">Cancel</button>
              </div>
            </form>
          </div>
        )}

        {isLoading && <SkeletonScreen rows={5} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && templates?.length === 0 && (
          <EmptyState icon={FolderOpen} heading="No folder templates" body="Create the first folder template." />
        )}

        {!isLoading && !error && templates && templates.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Name', 'Project Type', 'Items'].map((h) => (
                    <th key={h} scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {templates.map((tpl: FolderTemplate, i: number) => (
                  <tr
                    key={tpl.id}
                    className={`border-b border-surface-border last:border-0 hover:bg-surface-raised/50 transition-colors ${i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'}`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Link
                        href={`/admin/folder-templates/${tpl.id}`}
                        className="font-medium text-text-primary/80 hover:text-accent-saffron transition-colors"
                      >
                        {tpl.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-text-primary/50">
                      {tpl.project_type_id ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-text-primary/50 tabular-nums">
                      {tpl.items.length}
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
