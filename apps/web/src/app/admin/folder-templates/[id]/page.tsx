'use client'

import { use, useState } from 'react'
import { Plus, Pencil, FolderOpen } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import {
  useFolderTemplate,
  useUpdateFolderTemplate,
  useCreateFolderTemplateItem,
  useUpdateFolderTemplateItem,
} from '@/hooks/use-admin'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import type {
  FolderTemplateItem,
  CreateFolderTemplateItemPayload,
  UpdateFolderTemplateItemPayload,
} from '@/types'

const inputCls = 'px-3 py-2 text-sm bg-surface-base border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50'
const labelCls = 'text-xs font-semibold text-text-primary/60 uppercase tracking-wide'

export default function FolderTemplateDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const { data: user } = useMe()
  const { data: template, isLoading, error, refetch } = useFolderTemplate(id)
  const renameMutation = useUpdateFolderTemplate()
  const createItemMutation = useCreateFolderTemplateItem()
  const updateItemMutation = useUpdateFolderTemplateItem()

  const canManage = (user?.isSuperUser ?? false) || (user?.permissions.includes('template.manage') ?? false)

  // Template name edit
  const [editingName, setEditingName] = useState(false)
  const [nameInput, setNameInput] = useState('')
  const [nameError, setNameError] = useState('')

  function startEditName() {
    setNameInput(template?.name ?? '')
    setEditingName(true)
    setNameError('')
  }

  async function handleSaveName(e: React.FormEvent) {
    e.preventDefault()
    setNameError('')
    if (!nameInput.trim()) { setNameError('Name is required.'); return }
    try {
      await renameMutation.mutateAsync({ id, payload: { name: nameInput.trim() } })
      setEditingName(false)
    } catch (err) {
      setNameError(apiErrorMessage(err))
    }
  }

  // Add item
  const [showAddItem, setShowAddItem] = useState(false)
  const [addItemForm, setAddItemForm] = useState<CreateFolderTemplateItemPayload>({ name: '', sort_order: 0, parent_item_id: null })
  const [addItemError, setAddItemError] = useState('')

  async function handleAddItem(e: React.FormEvent) {
    e.preventDefault()
    setAddItemError('')
    if (!addItemForm.name.trim()) { setAddItemError('Folder name is required.'); return }
    try {
      await createItemMutation.mutateAsync({ templateId: id, payload: { ...addItemForm, parent_item_id: addItemForm.parent_item_id || null } })
      setShowAddItem(false)
      setAddItemForm({ name: '', sort_order: 0, parent_item_id: null })
    } catch (err) {
      setAddItemError(apiErrorMessage(err))
    }
  }

  // Edit item
  const [editingItemId, setEditingItemId] = useState<string | null>(null)
  const [editItemForm, setEditItemForm] = useState<UpdateFolderTemplateItemPayload>({})
  const [editItemError, setEditItemError] = useState('')

  function startEditItem(item: FolderTemplateItem) {
    setEditingItemId(item.id)
    setEditItemForm({ name: item.name, sort_order: item.sort_order, parent_item_id: item.parent_item_id })
    setEditItemError('')
  }

  async function handleSaveItem(e: React.FormEvent) {
    e.preventDefault()
    setEditItemError('')
    if (!editItemForm.name?.trim()) { setEditItemError('Name is required.'); return }
    try {
      await updateItemMutation.mutateAsync({ templateId: id, itemId: editingItemId!, payload: editItemForm })
      setEditingItemId(null)
    } catch (err) {
      setEditItemError(apiErrorMessage(err))
    }
  }

  // Build a parent-name map for display
  const parentNames: Record<string, string> = {}
  template?.items.forEach((item) => { parentNames[item.id] = item.name })

  return (
    <AppShell>
      <PageHeader
        title={template?.name ?? 'Template'}
        subtitle="Folder template items"
        actions={
          canManage ? (
            <button
              type="button"
              onClick={() => { setShowAddItem(true); setAddItemError('') }}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors"
            >
              <Plus size={16} aria-hidden="true" />
              Add Folder
            </button>
          ) : undefined
        }
      />

      <ContentArea>
        {isLoading && <SkeletonScreen rows={5} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && template && (
          <>
            {/* Template name */}
            <div className="mb-5 rounded-lg border border-surface-border bg-surface-raised p-4">
              {!editingName ? (
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className={`${labelCls} mb-1`}>Template Name</p>
                    <p className="text-text-primary/85 font-medium">{template.name}</p>
                    {template.project_type_id && (
                      <p className="text-xs font-mono text-text-primary/40 mt-0.5">Project type: {template.project_type_id}</p>
                    )}
                  </div>
                  {canManage && (
                    <button type="button" onClick={startEditName} aria-label="Edit template name" className="text-text-primary/30 hover:text-accent-saffron transition-colors">
                      <Pencil size={13} aria-hidden="true" />
                    </button>
                  )}
                </div>
              ) : (
                <form onSubmit={handleSaveName} className="flex flex-col gap-3 max-w-sm">
                  <div className="flex flex-col gap-1.5">
                    <label className={labelCls}>Name</label>
                    <input className={inputCls} value={nameInput} onChange={(e) => setNameInput(e.target.value)} />
                  </div>
                  {nameError && <p role="alert" className="text-xs text-accent-critical">{nameError}</p>}
                  <div className="flex gap-2">
                    <button type="submit" disabled={renameMutation.isPending} className="px-3 py-1.5 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
                      {renameMutation.isPending ? 'Saving…' : 'Save'}
                    </button>
                    <button type="button" onClick={() => setEditingName(false)} className="px-3 py-1.5 text-xs text-text-primary/50 hover:text-text-primary transition-colors">Cancel</button>
                  </div>
                </form>
              )}
            </div>

            {/* Add folder item */}
            {showAddItem && (
              <div className="mb-4">
                <h2 className="text-xs font-semibold text-text-primary/40 uppercase tracking-widest mb-3">New Folder</h2>
                <form onSubmit={handleAddItem} className="flex flex-col gap-3 p-4 bg-surface-base border border-surface-border rounded-lg max-w-lg">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="flex flex-col gap-1.5">
                      <label className={labelCls}>Folder Name <span className="text-accent-critical">*</span></label>
                      <input className={inputCls} value={addItemForm.name} onChange={(e) => setAddItemForm(f => ({ ...f, name: e.target.value }))} placeholder="Documents" />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className={labelCls}>Sort Order</label>
                      <input type="number" className={inputCls} value={addItemForm.sort_order} onChange={(e) => setAddItemForm(f => ({ ...f, sort_order: Number(e.target.value) }))} min={0} />
                    </div>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className={labelCls}>Parent Folder <span className="font-normal normal-case text-text-primary/30">(optional)</span></label>
                    <select
                      className={inputCls}
                      value={addItemForm.parent_item_id ?? ''}
                      onChange={(e) => setAddItemForm(f => ({ ...f, parent_item_id: e.target.value || null }))}
                    >
                      <option value="">— None (root) —</option>
                      {template.items.map((item) => (
                        <option key={item.id} value={item.id}>{item.name}</option>
                      ))}
                    </select>
                  </div>
                  {addItemError && <p role="alert" className="text-xs text-accent-critical">{addItemError}</p>}
                  <div className="flex gap-2">
                    <button type="submit" disabled={createItemMutation.isPending} className="px-3 py-1.5 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
                      {createItemMutation.isPending ? 'Adding…' : 'Add Folder'}
                    </button>
                    <button type="button" onClick={() => setShowAddItem(false)} className="px-3 py-1.5 text-xs text-text-primary/50 hover:text-text-primary transition-colors">Cancel</button>
                  </div>
                </form>
              </div>
            )}

            {/* Items list */}
            {template.items.length === 0 ? (
              <EmptyState icon={FolderOpen} heading="No folders" body="Add the first folder to this template." />
            ) : (
              <div className="overflow-x-auto rounded-lg border border-surface-border">
                <table className="w-full text-sm font-sans">
                  <thead>
                    <tr className="border-b border-surface-border bg-surface-raised">
                      {['Folder', 'Parent', 'Order', ''].map((h) => (
                        <th key={h} scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {template.items
                      .slice()
                      .sort((a, b) => a.sort_order - b.sort_order)
                      .map((item: FolderTemplateItem, i: number) => (
                        <tr
                          key={item.id}
                          className={`border-b border-surface-border last:border-0 ${i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'}`}
                        >
                          {editingItemId !== item.id ? (
                            <>
                              <td className="px-4 py-3 text-text-primary/80">{item.name}</td>
                              <td className="px-4 py-3 text-xs text-text-primary/45">
                                {item.parent_item_id ? (parentNames[item.parent_item_id] ?? item.parent_item_id.slice(0, 8)) : '—'}
                              </td>
                              <td className="px-4 py-3 font-mono text-xs text-text-primary/45 tabular-nums">{item.sort_order}</td>
                              <td className="px-4 py-3 text-right">
                                {canManage && (
                                  <button type="button" onClick={() => startEditItem(item)} aria-label={`Edit ${item.name}`} className="text-text-primary/30 hover:text-accent-saffron transition-colors">
                                    <Pencil size={12} aria-hidden="true" />
                                  </button>
                                )}
                              </td>
                            </>
                          ) : (
                            <td colSpan={4} className="px-4 py-3">
                              <form onSubmit={handleSaveItem} className="flex flex-col gap-2">
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                  <div className="flex flex-col gap-1">
                                    <label className={labelCls}>Name</label>
                                    <input className={inputCls} value={editItemForm.name ?? ''} onChange={(e) => setEditItemForm(f => ({ ...f, name: e.target.value }))} />
                                  </div>
                                  <div className="flex flex-col gap-1">
                                    <label className={labelCls}>Parent</label>
                                    <select className={inputCls} value={editItemForm.parent_item_id ?? ''} onChange={(e) => setEditItemForm(f => ({ ...f, parent_item_id: e.target.value || null }))}>
                                      <option value="">— Root —</option>
                                      {template.items.filter((x) => x.id !== item.id).map((x) => (
                                        <option key={x.id} value={x.id}>{x.name}</option>
                                      ))}
                                    </select>
                                  </div>
                                  <div className="flex flex-col gap-1">
                                    <label className={labelCls}>Order</label>
                                    <input type="number" className={inputCls} value={editItemForm.sort_order ?? 0} onChange={(e) => setEditItemForm(f => ({ ...f, sort_order: Number(e.target.value) }))} min={0} />
                                  </div>
                                </div>
                                {editItemError && <p role="alert" className="text-xs text-accent-critical">{editItemError}</p>}
                                <div className="flex gap-2">
                                  <button type="submit" disabled={updateItemMutation.isPending} className="px-3 py-1.5 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
                                    {updateItemMutation.isPending ? 'Saving…' : 'Save'}
                                  </button>
                                  <button type="button" onClick={() => setEditingItemId(null)} className="px-3 py-1.5 text-xs text-text-primary/50 hover:text-text-primary transition-colors">Cancel</button>
                                </div>
                              </form>
                            </td>
                          )}
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </ContentArea>
    </AppShell>
  )
}
