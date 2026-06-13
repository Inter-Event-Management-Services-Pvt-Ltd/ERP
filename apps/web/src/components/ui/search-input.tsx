'use client'

import { useEffect, useRef, useState } from 'react'
import { Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  debounceMs?: number
}

export function SearchInput({
  value,
  onChange,
  placeholder = 'Search…',
  className,
  debounceMs = 200,
}: SearchInputProps) {
  const [local, setLocal] = useState(value)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    setLocal(value)
  }, [value])

  function handleChange(next: string) {
    setLocal(next)
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => onChange(next), debounceMs)
  }

  return (
    <div className={cn('relative', className)}>
      <Search
        size={14}
        className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-primary/30 pointer-events-none"
        aria-hidden="true"
      />
      <input
        type="search"
        value={local}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={placeholder}
        className={cn(
          'w-full rounded-md border border-surface-border bg-surface-base pl-8 pr-8 py-2',
          'text-sm font-sans text-text-primary placeholder:text-text-primary/30',
          'focus:outline-none focus:ring-2 focus:ring-accent-saffron focus:ring-offset-1 focus:ring-offset-surface-raised',
          'transition-colors duration-100'
        )}
      />
      {local && (
        <button
          type="button"
          onClick={() => handleChange('')}
          aria-label="Clear search"
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-primary/30 hover:text-text-primary/60 transition-colors"
        >
          <X size={14} aria-hidden="true" />
        </button>
      )}
    </div>
  )
}
