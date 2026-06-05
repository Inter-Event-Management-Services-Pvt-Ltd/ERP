'use client'

import { useState } from 'react'
import { ChevronRight, Folder, FolderOpen } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FolderNode } from '@/types'

interface FolderNodeItemProps {
  node: FolderNode
  depth: number
  selectedId: string | null
  onSelect: (id: string) => void
}

function FolderNodeItem({ node, depth, selectedId, onSelect }: FolderNodeItemProps) {
  const [expanded, setExpanded] = useState(depth === 0)
  const hasChildren = node.children.length > 0
  const isSelected = node.id === selectedId

  return (
    <div>
      <button
        type="button"
        onClick={() => {
          if (hasChildren) setExpanded((e) => !e)
          onSelect(node.id)
        }}
        aria-expanded={hasChildren ? expanded : undefined}
        className={cn(
          'flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-left text-sm font-sans transition-colors duration-100',
          isSelected
            ? 'bg-accent-madder/30 text-text-primary'
            : 'text-text-primary/60 hover:bg-surface-raised hover:text-text-primary'
        )}
        style={{ paddingLeft: `${0.5 + depth * 1}rem` }}
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
        {expanded && hasChildren ? (
          <FolderOpen size={14} aria-hidden="true" className="flex-none text-accent-saffron" />
        ) : (
          <Folder size={14} aria-hidden="true" className="flex-none text-accent-saffron/70" />
        )}
        <span className="truncate">{node.name}</span>
      </button>

      {hasChildren && expanded && (
        <div>
          {node.children
            .slice()
            .sort((a, b) => a.sort_order - b.sort_order)
            .map((child) => (
              <FolderNodeItem
                key={child.id}
                node={child}
                depth={depth + 1}
                selectedId={selectedId}
                onSelect={onSelect}
              />
            ))}
        </div>
      )}
    </div>
  )
}

interface FolderTreePanelProps {
  root: FolderNode
  selectedId: string | null
  onSelect: (id: string) => void
}

export function FolderTreePanel({ root, selectedId, onSelect }: FolderTreePanelProps) {
  return (
    <nav aria-label="Folder tree" className="space-y-0.5 py-1">
      <FolderNodeItem
        node={root}
        depth={0}
        selectedId={selectedId}
        onSelect={onSelect}
      />
    </nav>
  )
}
