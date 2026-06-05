'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, FileText } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { EmptyState } from '@/components/states/empty-state'
import { FolderTreePanel } from '@/components/projects/folder-tree-panel'
import { useProject } from '@/hooks/use-projects'
import { useFolderTree } from '@/hooks/use-folder-tree'

interface Props {
  params: Promise<{ id: string }>
}

export default function ProjectDocumentsPage({ params }: Props) {
  const { id } = use(params)
  const { data: project } = useProject(id)
  const { data: tree, isLoading: treeLoading, error: treeError } = useFolderTree(id)

  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null)

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
        <aside
          className="w-56 flex-none border-r border-surface-border bg-surface-deep overflow-y-auto"
          aria-label="Folder navigation"
        >
          <div className="px-3 pt-3 pb-2">
            <p className="text-xs font-sans font-semibold text-text-primary/40 uppercase tracking-wider mb-1">
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
            <p className="px-3 text-xs text-text-primary/30 font-sans py-2">
              No folders
            </p>
          )}

          {!treeLoading && tree && (
            <FolderTreePanel
              root={tree}
              selectedId={selectedFolderId}
              onSelect={setSelectedFolderId}
            />
          )}
        </aside>

        <main className="flex-1 overflow-y-auto p-5">
          {!selectedFolderId ? (
            <EmptyState
              heading="Select a folder"
              body="Choose a folder from the sidebar to view its documents."
            />
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-xs font-mono text-text-primary/40">
                <FileText size={12} aria-hidden="true" />
                <span>Folder: {selectedFolderId}</span>
              </div>
              {/* Document list — POST /v1/folders/{id}/documents and GET
                  endpoints are Phase 3 scope (OPEN-018). */}
              <EmptyState
                heading="Documents coming in Phase 3"
                body="File upload and document listing will be available once the document endpoints are implemented."
              />
            </div>
          )}
        </main>
      </div>
    </AppShell>
  )
}
