'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { EmptyState } from '@/components/states/empty-state'
import { FolderTreePanel } from '@/components/projects/folder-tree-panel'
import { DocumentListPanel } from '@/components/projects/document-list-panel'
import { ArchiveExportPanel } from '@/components/projects/archive-export-panel'
import { useProject } from '@/hooks/use-projects'
import { useFolderTree } from '@/hooks/use-folder-tree'
import { useMe } from '@/hooks/use-me'

interface Props {
  params: Promise<{ id: string }>
}

function findFolderName(id: string | null, root: { id: string; name: string; children: { id: string; name: string; children: unknown[] }[] } | undefined): string {
  if (!id || !root) return ''
  if (root.id === id) return root.name
  for (const child of root.children) {
    const found = findFolderName(id, child as Parameters<typeof findFolderName>[1])
    if (found) return found
  }
  return id
}

export default function ProjectDocumentsPage({ params }: Props) {
  const { id } = use(params)
  const { data: user } = useMe()
  const { data: project } = useProject(id)
  const { data: tree, isLoading: treeLoading, error: treeError } = useFolderTree(id)

  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null)

  const canManage =
    (user?.isSuperUser || user?.permissions.includes('project.manage')) ?? false
  const canUpload =
    (user?.isSuperUser || user?.permissions.includes('document.upload')) ?? false
  const canExport =
    (user?.isSuperUser || user?.permissions.includes('archive.export')) ?? false

  const selectedFolderName = findFolderName(
    selectedFolderId,
    tree as Parameters<typeof findFolderName>[1]
  )

  return (
    <AppShell>
      <PageHeader
        title="Documents"
        subtitle={
          <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-text-primary/40 font-sans">
            <Link href="/projects" className="hover:text-text-primary/70 transition-colors">
              Projects
            </Link>
            <ChevronRight size={12} aria-hidden="true" />
            {project ? (
              <Link
                href={`/projects/${id}`}
                className="hover:text-text-primary/70 transition-colors"
              >
                {project.name}
              </Link>
            ) : (
              <span>Project</span>
            )}
            <ChevronRight size={12} aria-hidden="true" />
            <span className="text-text-primary/60">Documents</span>
          </nav>
        }
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside
          className="w-60 flex-none border-r border-surface-border bg-surface-deep overflow-y-auto flex flex-col"
          aria-label="Folder navigation"
        >
          <div className="px-3 pt-3 pb-2 flex-none">
            <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider">
              Folders
            </p>
          </div>

          {treeLoading && (
            <div className="px-3 space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="h-6 rounded bg-surface-border/50 shimmer"
                  style={{ width: `${60 + (i % 3) * 15}%` }}
                />
              ))}
            </div>
          )}

          {!treeLoading && treeError && (
            <p className="px-3 text-xs text-accent-critical font-sans py-2">
              Failed to load folders
            </p>
          )}

          {!treeLoading && !treeError && !tree && (
            <p className="px-3 text-xs text-text-primary/30 font-sans py-2">No folders</p>
          )}

          {!treeLoading && tree && (
            <div className="flex-1">
              <FolderTreePanel
                root={tree}
                selectedId={selectedFolderId}
                onSelect={setSelectedFolderId}
                projectId={id}
                canManage={canManage}
              />
            </div>
          )}

          {/* Archive export section */}
          {(canExport || true) && (
            <div className="flex-none border-t border-surface-border/50 px-3 py-3 mt-2">
              <ArchiveExportPanel projectId={id} canExport={canExport} />
            </div>
          )}
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-5">
          {!selectedFolderId ? (
            <EmptyState
              heading="Select a folder"
              body="Choose a folder from the sidebar to view its documents."
            />
          ) : (
            <DocumentListPanel
              folderId={selectedFolderId}
              folderName={selectedFolderName}
              projectId={id}
              canUpload={canUpload}
            />
          )}
        </main>
      </div>
    </AppShell>
  )
}
