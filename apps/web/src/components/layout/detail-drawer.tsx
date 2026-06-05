'use client'

import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DetailDrawerProps {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  className?: string
}

export function DetailDrawer({ open, onClose, title, children, className }: DetailDrawerProps) {
  const closeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (open) closeRef.current?.focus()
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  return (
    <aside
      aria-label={title}
      aria-hidden={!open}
      className={cn(
        'flex-none bg-surface-deep border-l border-surface-border overflow-y-auto',
        'transition-[width] duration-220 ease-out',
        open ? 'w-[260px]' : 'w-0',
        className
      )}
    >
      {open && (
        <div className="p-4 min-w-[260px]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-serif italic text-base text-text-primary truncate">
              {title}
            </h2>
            <button
              ref={closeRef}
              onClick={onClose}
              aria-label="Close panel"
              className="p-1 rounded hover:bg-surface-raised text-text-primary/50 hover:text-text-primary transition-colors flex-none ml-2"
            >
              <X size={15} aria-hidden="true" />
            </button>
          </div>
          {children}
        </div>
      )}
    </aside>
  )
}
