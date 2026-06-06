'use client'

import { useState, useRef, KeyboardEvent } from 'react'
import { ChevronRight, Folder, FolderOpen, Plus, Pencil, Trash2, Loader2 } from 'lucide-react'
import { ConfirmDialog } from '@/components/status/confirm-dialog'
import { useCreateFolder, useRenameFolder, useDeleteFolder } from '@/hooks/use-folders'
import { apiErrorMessage } from '@/lib/errors'
import { cn } from '@/lib/utils'
import type { FolderNode } from '@/types'

interface FolderTreePanelProps {
  root: FolderNode
  selectedId: string | null
  onSelect: (id: string) => void
  projectId?: string
  canManage?: boolean
}

export function FolderTreePanel({
  root,
  selectedId,
  onSelect,
  projectId = '',
  canManage = false,
}: FolderTreePanelProps) {
  return (
    <nav aria-label="Folder tree" className="space-y-0.5 py-1">
      <FolderNodeItem
        node={root}
        depth={0}
        selectedId={selectedId}
        onSelect={onSelect}
        projectId={projectId}
        canManage={canManage}
        isRoot
      />
    </nav>
  )
}

interface NodeProps {
  node: FolderNode
  depth: number
  selectedId: string | null
  onSelect: (id: string) => void
  projectId: string
  canManage: boolean
  isRoot?: boolean
}

function FolderNodeItem({
  node,
  depth,
  selectedId,
  onSelect,
  projectId,
  canManage,
  isRoot = false,
}: NodeProps) {
  const [expanded, setExpanded] = useState(depth === 0)
  const [isRenaming, setIsRenaming] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [renameValue, setRenameValue] = useState(node.name)
  const [newFolderName, setNewFolderName] = useState('')
  const [pendingDelete, setPendingDelete] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const renameRef = useRef<HTMLInputElement>(null)
  const createRef = useRef<HTMLInputElement>(null)

  const { mutate: create, isPending: creating } = useCreateFolder(projectId)
  const { mutate: rename, isPending: renaming } = useRenameFolder(projectId)
  const { mutate: remove, isPending: deleting } = useDeleteFolder(projectId)

  const hasChildren = node.children.length > 0 || isCreating
  const isSelected = node.id === selectedId

  function startCreate() {
    setIsCreating(true)
    setExpanded(true)
    setNewFolderName('')
    setTimeout(() => createRef.current?.focus(), 0)
  }

  function startRename() {
    setIsRenaming(true)
    setRenameValue(node.name)
    setTimeout(() => renameRef.current?.select(), 0)
  }

  function cancelRename() {
    setIsRenaming(false)
    setRenameValue(node.name)
    setActionError(null)
  }

  function cancelCreate() {
    setIsCreating(false)
    setNewFolderName('')
    setActionError(null)
  }

  function submitRename() {
    const trimmed = renameValue.trim()
    if (!trimmed || trimmed === node.name) { cancelRename(); return }
    setActionError(null)
    rename(
      { folderId: node.id, payload: { name: trimmed } },
      {
        onSuccess: () => setIsRenaming(false),
        onError: (err) => setActionError(apiErrorMessage(err)),
      }
    )
  }

  function submitCreate() {
    const trimmed = newFolderName.trim()
    if (!trimmed) { cancelCreate(); return }
    setActionError(null)
    create(
      { name: trimmed, parent_folder_id: node.id },
      {
        onSuccess: () => { setIsCreating(false); setNewFolderName('') },
        onError: (err) => setActionError(apiErrorMessage(err)),
      }
    )
  }

  function handleDeleteConfirm() {
    setPendingDelete(false)
    setActionError(null)
    remove(node.id, {
      onError: (err) => setActionError(apiErrorMessage(err)),
    })
  }

  function handleRenameKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') submitRename()
    if (e.key === 'Escape') cancelRename()
  }

  function handleCreateKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') submitCreate()
    if (e.key === 'Escape') cancelCreate()
  }

  const sortedChildren = node.children
    .slice()
    .sort((a, b) => a.sort_order - b.sort_order)

  return (
    <div>
      <div className="group relative">
        {isRenaming ? (
          <div className="flex items-center gap-1 px-2 py-1" style={{ paddingLeft: `${0.5 + depth * 1}rem` }}>
            <Folder size={14} className="flex-none text-accent-saffron" aria-hidden="true" />
            <input
              ref={renameRef}
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={handleRenameKey}
              onBlur={submitRename}
              disabled={renaming}
              className="flex-1 min-w-0 text-sm font-sans bg-surface-base border border-accent-saffron/40 rounded px-1 py-0.5 text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-saffron disabled:opacity-50"
              aria-label="Folder name"
            />
          </div>
        ) : (
          <div
            className={cn(
              'flex items-center rounded-md transition-colors duration-100',
              isSelected
                ? 'bg-accent-madder/30'
                : 'hover:bg-surface-raised'
            )}
            style={{ paddingLeft: `${0.5 + depth * 1}rem` }}
          >
            <button
              type="button"
              onClick={() => {
                if (hasChildren) setExpanded((e) => !e)
                onSelect(node.id)
              }}
              aria-expanded={hasChildren ? expanded : undefined}
              className={cn(
                'flex flex-1 min-w-0 items-center gap-1.5 py-1.5 pr-1 text-left text-sm font-sans',
                isSelected ? 'text-text-primary' : 'text-text-primary/60 group-hover:text-text-primary'
              )}
            >
              {hasChildren ? (
                <ChevronRight
                  size={12}
                  aria-hidden="true"
                  className={cn(
                    'flex-none transition-transform duration-180',
                    expanded && 'rotate-90'
                  )}
                />
              ) : (
                <span className="w-3 flex-none" aria-hidden="true" />
              )}
              {expanded && node.children.length > 0 ? (
                <FolderOpen size={14} aria-hidden="true" className="flex-none text-accent-saffron" />
              ) : (
                <Folder size={14} aria-hidden="true" className="flex-none text-accent-saffron/70" />
              )}
              <span className="truncate flex-1">{node.name}</span>
            </button>

            {canManage && (
              <span className="flex-none flex items-center gap-0.5 pr-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <ActionBtn
                  icon={<Plus size={11} />}
                  label={`Add subfolder in ${node.name}`}
                  onClick={startCreate}
                />
                {!isRoot && (
                  <>
                    <ActionBtn
                      icon={<Pencil size={11} />}
                      label={`Rename ${node.name}`}
                      onClick={startRename}
                    />
                    <ActionBtn
                      icon={deleting ? <Loader2 size={11} className="animate-spin" /> : <Trash2 size={11} />}
                      label={`Delete ${node.name}`}
                      onClick={() => setPendingDelete(true)}
                      danger
                      disabled={deleting}
                    />
                  </>
                )}
              </span>
            )}
          </div>
        )}

        {actionError && (
          <p className="text-xs text-accent-critical font-sans px-2 pb-1" role="alert">
            {actionError}
          </p>
        )}
      </div>

      {expanded && (
        <div>
          {sortedChildren.map((child) => (
            <FolderNodeItem
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              projectId={projectId}
              canManage={canManage}
            />
          ))}

          {isCreating && (
            <div
              className="flex items-center gap-1 px-2 py-1"
              style={{ paddingLeft: `${0.5 + (depth + 1) * 1}rem` }}
            >
              <Folder size={14} className="flex-none text-accent-saffron/50" aria-hidden="true" />
              <input
                ref={createRef}
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={handleCreateKey}
                onBlur={submitCreate}
                disabled={creating}
                placeholder="Folder name…"
                className="flex-1 min-w-0 text-sm font-sans bg-surface-base border border-accent-saffron/40 rounded px-1 py-0.5 text-text-primary placeholder:text-text-primary/30 focus:outline-none focus:ring-1 focus:ring-accent-saffron disabled:opacity-50"
                aria-label="New folder name"
              />
            </div>
          )}
        </div>
      )}

      <ConfirmDialog
        open={pendingDelete}
        title="Delete folder?"
        description={`"${node.name}" will be removed. The folder must be empty — if it contains subfolders or documents the backend will reject this.`}
        confirmLabel="Delete"
        destructive
        onConfirm={handleDeleteConfirm}
        onCancel={() => setPendingDelete(false)}
      />
    </div>
  )
}

function ActionBtn({
  icon,
  label,
  onClick,
  danger = false,
  disabled = false,
}: {
  icon: React.ReactNode
  label: string
  onClick: () => void
  danger?: boolean
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      className={cn(
        'p-0.5 rounded transition-colors disabled:opacity-40',
        danger
          ? 'text-text-primary/30 hover:text-accent-critical'
          : 'text-text-primary/30 hover:text-accent-saffron'
      )}
    >
      {icon}
    </button>
  )
}
